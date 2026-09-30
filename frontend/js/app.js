"use strict";

// La interfaz consume la API existente. La inferencia y la búsqueda siguen en Python.
const app = {
  reglas: [],
  curvas: null,
  variable: "temperatura_rack",
  conjunto: "ALTA",
  tab: "tabFIS",
  detalle: false,
  salida: null,
  entradasEvaluadas: null,
  estadoCargado: false,
  optimizado: false,
  ocupado: false,
  frame: null,
  variables: {
    temperatura_rack: { nombre: "Temperatura del rack", unidad: "°C", canvas: "miniCanvasRack", input: "inputRack", conjuntos: ["BAJA", "OPTIMA", "ALTA", "CRITICA"] },
    uso_cpu: { nombre: "Uso de CPU", unidad: "%", canvas: "miniCanvasCpu", input: "inputCpu", conjuntos: ["BAJO", "MEDIO", "ALTO"] },
    temperatura_exterior: { nombre: "Temperatura exterior", unidad: "°C", canvas: "miniCanvasExt", input: "inputExterior", conjuntos: ["FRIO", "TEMPLADO", "CALIDO"] },
    potencia_enfriamiento: { nombre: "Potencia de enfriamiento", unidad: "%", conjuntos: ["MINIMA", "MEDIA", "ALTA", "MAXIMA"] }
  },
  colores: { BAJA: "#24b46b", OPTIMA: "#e55357", ALTA: "#009ddb", CRITICA: "#e9af13", BAJO: "#eb9c19", MEDIO: "#e55357", ALTO: "#009ddb", FRIO: "#eb9c19", TEMPLADO: "#e55357", CALIDO: "#009ddb", MINIMA: "#009ddb", MEDIA: "#24b46b", MAXIMA: "#e55357" },

  el(id) { return document.getElementById(id); },
  numero(value, digits = 1) {
    return new Intl.NumberFormat("es-EC", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value);
  },
  color(variable, name) {
    return variable === "potencia_enfriamiento" && name === "ALTA" ? "#ed9f18" : (this.colores[name] || "#007da5");
  },

  init() {
    document.querySelectorAll(".workspace-tab").forEach(button => {
      button.addEventListener("click", () => this.activarTab(button.dataset.tab));
      button.addEventListener("keydown", event => {
        const tabs = [...document.querySelectorAll(".workspace-tab")];
        let index = tabs.indexOf(button);
        if (event.key === "ArrowRight") index = (index + 1) % tabs.length;
        else if (event.key === "ArrowLeft") index = (index + tabs.length - 1) % tabs.length;
        else if (event.key === "Home") index = 0;
        else if (event.key === "End") index = tabs.length - 1;
        else return;
        event.preventDefault();
        this.activarTab(tabs[index].dataset.tab);
        tabs[index].focus();
      });
    });
    document.querySelectorAll("[data-variable]").forEach(block => {
      block.addEventListener("click", () => this.seleccionarVariable(block.dataset.variable, true));
    });
    this.el("selectVariable").addEventListener("change", event => this.seleccionarVariable(event.target.value, this.detalle));
    this.el("selectConjunto").addEventListener("change", event => this.seleccionarConjunto(event.target.value));
    this.el("btnVerPertenencia").addEventListener("click", () => this.mostrarDetalle(true));
    this.el("btnVolverDiagrama").addEventListener("click", () => this.mostrarDetalle(false));
    this.el("blockMamdani").addEventListener("click", () => this.activarTab("tabReglas"));
    this.el("formInferencia").addEventListener("submit", event => { event.preventDefault(); this.ejecutarInferencia(); });
    this.el("formGenetico").addEventListener("submit", event => { event.preventDefault(); this.ejecutarGenetico(); });
    this.el("formInferencia").addEventListener("input", () => {
      this.actualizarVectorEntradas();
      this.salida = null;
      this.entradasEvaluadas = null;
      this.el("fisOutputValCentroid").textContent = "z* = — %";
      this.el("descripcionSalida").textContent = "Pulsa ▶ para evaluar las entradas";
      this.programarDibujo();
    });
    this.el("selectFiltroRack").addEventListener("change", () => this.renderizarReglas());
    this.el("buscarReglas").addEventListener("input", () => this.renderizarReglas());
    this.el("btnReintentar").addEventListener("click", () => this.cargarModelo());
    const observer = new ResizeObserver(() => this.programarDibujo());
    observer.observe(this.el("fisCanvasArea"));
    observer.observe(this.el("canvasPertenencia").parentElement);
    window.addEventListener("resize", () => this.programarDibujo());
    this.cargarModelo();
  },

  async pedir(ruta, datos) {
    let response;
    try {
      response = await fetch(ruta, datos === undefined ? {} : {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(datos)
      });
    } catch (_) { throw new Error("No se pudo conectar con el controlador. Comprueba que la aplicación esté en ejecución."); }
    let json;
    try { json = await response.json(); }
    catch (_) { throw new Error(`El controlador devolvió una respuesta no válida (${response.status}).`); }
    if (!response.ok || json.error) throw new Error(json.error || `El controlador devolvió un error (${response.status}).`);
    return json;
  },

  async cargarModelo() {
    if (this.ocupado) return;
    this.setOcupado(true);
    this.limpiarError();
    this.status("Cargando la tabla y las funciones del controlador…", "busy");
    // Las curvas son una lectura; la simulación de estado termina antes de inferir.
    const [estado, curvas] = await Promise.allSettled([this.pedir("/api/estado"), this.pedir("/api/curvas-pertenencia")]);
    let error = null;
    if (estado.status === "fulfilled") {
      // La API de estado no informa el origen de la tabla; al reconectar
      // mostramos "Tabla activa", incluso si el servidor se reinició.
      this.optimizado = false;
      this.actualizarModelo(estado.value);
      this.estadoCargado = true;
    } else error = estado.reason;
    if (curvas.status === "fulfilled") {
      this.curvas = curvas.value;
      this.seleccionarVariable(this.variable, this.detalle);
    } else error = curvas.reason;
    this.setOcupado(false);
    if (error) this.mostrarError(error.message);
    else await this.ejecutarInferencia();
  },

  actualizarModelo(data) {
    this.reglas = Array.isArray(data.reglas) ? data.reglas : [];
    const total = this.reglas.length;
    this.el("fisBadgeReglas").textContent = `${total} reglas`;
    this.el("totalReglasSidebar").textContent = total;
    this.el("estadoReglas").textContent = this.optimizado ? "Optimizada con AG" : "Tabla activa";
    this.el("descripcionReglas").textContent = this.optimizado ? "Consecuentes de la mejor tabla encontrada por el algoritmo genético." : "Reglas de la tabla cargada en el controlador Mamdani.";
    this.el("fuenteResultados").textContent = this.optimizado ? "Tabla optimizada · Simulación de 24 h" : "Tabla activa · Simulación de 24 h";
    const costo = data.kpis?.costo_diario;
    const consumo = data.kpis?.consumo_kwh;
    this.el("kpiCostoDiario").textContent = Number.isFinite(costo) ? `$ ${this.numero(costo, 2)}` : "—";
    this.el("kpiConsumoKwh").textContent = Number.isFinite(consumo) ? this.numero(consumo, 2) : "—";
    this.renderizarReglas();
  },

  setOcupado(value) {
    this.ocupado = value;
    this.el("btnReintentar").disabled = value;
    this.el("btnEjecutarGA").disabled = value || !this.estadoCargado;
    this.el("btnCalcularInferencia").disabled = value || !this.estadoCargado;
    document.querySelectorAll("#formInferencia input, #formGenetico input").forEach(input => { input.disabled = value; });
    const sinCurvas = !this.curvas;
    this.el("selectVariable").disabled = sinCurvas;
    this.el("selectConjunto").disabled = sinCurvas;
    this.el("btnVerPertenencia").disabled = sinCurvas;
  },

  activarTab(id) {
    this.tab = id;
    document.querySelectorAll(".workspace-tab").forEach(button => {
      const selected = button.dataset.tab === id;
      button.classList.toggle("active", selected);
      button.setAttribute("aria-selected", String(selected));
      button.tabIndex = selected ? 0 : -1;
    });
    this.el("tabFIS").hidden = id !== "tabFIS";
    this.el("tabReglas").hidden = id !== "tabReglas";
    this.el("panelPertenencia").hidden = id !== "tabFIS";
    this.el("panelGenetico").hidden = id !== "tabReglas";
    this.programarDibujo();
  },

  seleccionarVariable(variable, detalle) {
    if (!this.curvas?.[variable]) return;
    this.variable = variable;
    this.el("selectVariable").value = variable;
    const nombres = this.nombresConjuntos(variable);
    if (!nombres.includes(this.conjunto)) this.conjunto = nombres[0];
    this.el("selectConjunto").replaceChildren(...nombres.map(name => {
      const option = document.createElement("option"); option.value = name; option.textContent = name; return option;
    }));
    this.el("selectConjunto").value = this.conjunto;
    document.querySelectorAll("[data-variable]").forEach(block => block.classList.toggle("selected", block.dataset.variable === variable));
    this.actualizarInspector();
    this.mostrarDetalle(detalle);
  },
  seleccionarConjunto(name) {
    this.conjunto = name;
    this.el("selectConjunto").value = name;
    this.actualizarInspector();
    this.renderizarLeyenda();
    this.programarDibujo();
  },
  nombresConjuntos(variable) {
    return this.variables[variable].conjuntos.filter(name => this.curvas[variable].conjuntos[name]);
  },

  // Reconstruye los vértices de las curvas lineales muestreadas por la API.
  // No modifica parámetros ni duplica la definición del controlador.
  obtenerVertices(data, name) {
    const y = data.conjuntos[name], x = data.x;
    const positivos = y.map((value, index) => value > 0 ? index : -1).filter(index => index >= 0);
    const cima = y.map((value, index) => value === 1 ? index : -1).filter(index => index >= 0);
    if (!positivos.length || !cima.length) return null;
    const a = x[Math.max(0, positivos[0] - 1)];
    const b = x[cima[0]], c = x[cima[cima.length - 1]];
    const d = x[Math.min(x.length - 1, positivos[positivos.length - 1] + 1)];
    return b === c ? [a, b, d] : [a, b, c, d];
  },
  actualizarInspector() {
    const vertices = this.obtenerVertices(this.curvas[this.variable], this.conjunto);
    this.el("tipoFuncion").textContent = !vertices ? "Curva muestreada" : vertices.length === 3 ? "Triangular" : "Trapezoidal";
    this.el("coordenadasConjunto").replaceChildren();
    if (!vertices) { this.el("vectorConjunto").textContent = "Sin vértices disponibles"; return; }
    const labels = vertices.length === 3 ? ["Inicio base (a)", "Vértice / pico (b)", "Fin base (c)"] : ["Inicio base (a)", "Inicio cima (b)", "Fin cima (c)", "Fin base (d)"];
    vertices.forEach((value, index) => {
      const row = document.createElement("div"); row.className = "field-row";
      const label = document.createElement("span"); label.textContent = labels[index];
      const output = document.createElement("output"); output.className = "coordinate-value"; output.textContent = `${this.numero(value)} ${this.variables[this.variable].unidad}`;
      row.append(label, output); this.el("coordenadasConjunto").append(row);
    });
    this.el("etiquetaVector").textContent = vertices.length === 3 ? "Vector [a, b, c]" : "Vector [a, b, c, d]";
    this.el("vectorConjunto").textContent = `[${vertices.join(", ")}]`;
  },
  mostrarDetalle(value) {
    this.detalle = value;
    this.el("vistaDiagrama").hidden = value;
    this.el("vistaPertenencia").hidden = !value;
    this.el("btnVolverDiagrama").hidden = !value;
    this.el("tituloVistaFIS").textContent = value ? `${this.variable === "potencia_enfriamiento" ? "Salida" : "Entrada"}: ${this.variables[this.variable].nombre}` : "Sistema de inferencia difusa";
    this.el("descripcionVistaFIS").textContent = value ? `${this.variable} · Funciones de pertenencia del controlador` : "Selecciona una variable para ver sus funciones de pertenencia.";
    if (value) this.renderizarLeyenda();
    this.programarDibujo();
  },
  renderizarLeyenda() {
    if (!this.curvas) return;
    this.el("leyendaPertenencia").replaceChildren(...this.nombresConjuntos(this.variable).map(name => {
      const button = document.createElement("button"); button.className = `legend-item${name === this.conjunto ? " active" : ""}`;
      button.setAttribute("aria-pressed", String(name === this.conjunto));
      const swatch = document.createElement("span"); swatch.className = "legend-swatch"; swatch.style.background = this.color(this.variable, name);
      button.append(swatch, document.createTextNode(name)); button.addEventListener("click", () => this.seleccionarConjunto(name)); return button;
    }));
    this.el("notaPertenencia").textContent = `Universo: ${this.curvas[this.variable].x[0]} – ${this.curvas[this.variable].x.at(-1)} ${this.variables[this.variable].unidad}. Los grados de pertenencia están entre 0 y 1.`;
    this.el("canvasPertenencia").setAttribute("aria-label", `Pertenencias de ${this.variables[this.variable].nombre}: ${this.nombresConjuntos(this.variable).join(", ")}`);
  },

  renderizarReglas() {
    const filtro = this.el("selectFiltroRack").value;
    const busqueda = this.el("buscarReglas").value.trim().toUpperCase();
    const rows = this.reglas.filter(regla => {
      const ant = regla.antecedentes;
      const texto = `temperatura_rack ${ant.temperatura_rack} uso_cpu ${ant.uso_cpu} temperatura_exterior ${ant.temperatura_exterior} potencia_enfriamiento ${regla.etiqueta_consecuente}`;
      return (filtro === "TODOS" || ant.temperatura_rack === filtro) && texto.toUpperCase().includes(busqueda);
    });
    this.el("tbodyReglas36").replaceChildren(...rows.map(regla => {
      const tr = document.createElement("tr"), id = document.createElement("td"), expression = document.createElement("td"), gene = document.createElement("td");
      id.textContent = regla.identificador;
      expression.className = "rule-expression";
      const keyword = text => { const span = document.createElement("span"); span.className = "rule-keyword"; span.textContent = text; return span; };
      const ant = regla.antecedentes;
      expression.append(keyword("SI "), document.createTextNode(`temperatura_rack = ${ant.temperatura_rack} `), keyword("Y "), document.createTextNode(`uso_cpu = ${ant.uso_cpu} `), keyword("Y "), document.createTextNode(`temperatura_exterior = ${ant.temperatura_exterior} `), keyword("ENTONCES "), document.createTextNode("potencia_enfriamiento = "));
      const consecuente = document.createElement("span"); consecuente.className = "consequent"; consecuente.dataset.level = regla.nivel; consecuente.textContent = regla.etiqueta_consecuente; expression.append(consecuente);
      const badge = document.createElement("span"); badge.className = "gene-value"; badge.textContent = regla.nivel; gene.append(badge);
      tr.append(id, expression, gene); return tr;
    }));
    this.el("contadorReglas").textContent = `${rows.length} / ${this.reglas.length} reglas`;
    this.el("reglasVacias").hidden = rows.length !== 0;
  },

  actualizarVectorEntradas() {
    this.el("vectorEntradas").textContent = `[${["inputRack", "inputCpu", "inputExterior"].map(id => this.el(id).value || "—").join(", ")}]`;
  },
  async ejecutarInferencia() {
    if (this.ocupado || !this.estadoCargado || !this.el("formInferencia").reportValidity()) return;
    const datos = { temperatura_rack: this.el("inputRack").valueAsNumber, uso_cpu: this.el("inputCpu").valueAsNumber, temperatura_exterior: this.el("inputExterior").valueAsNumber };
    this.setOcupado(true);
    this.limpiarError();
    this.status("Calculando la inferencia Mamdani…", "busy");
    try {
      const data = await this.pedir("/api/inferencia", datos);
      if (!Number.isFinite(data.potencia_enfriamiento)) throw new Error("No se recibió una potencia válida del controlador.");
      this.salida = data;
      this.entradasEvaluadas = datos;
      this.el("fisOutputValCentroid").textContent = `z* = ${this.numero(data.potencia_enfriamiento)} %`;
      this.el("descripcionSalida").textContent = data.curva_agregada?.x?.length ? "Salida agregada · Centroide" : "Centroide · Curva no disponible";
      this.el("canvasSalida").setAttribute("aria-label", `Salida de inferencia: ${this.numero(data.potencia_enfriamiento)} por ciento de potencia`);
      this.status("Inferencia calculada. La tabla del controlador está sincronizada.");
    } catch (error) {
      this.salida = null; this.entradasEvaluadas = null;
      this.el("fisOutputValCentroid").textContent = "z* = — %";
      this.el("descripcionSalida").textContent = "No se pudo calcular la salida";
      this.mostrarError(error.message);
    } finally { this.setOcupado(false); this.programarDibujo(); }
  },
  async ejecutarGenetico() {
    if (this.ocupado || !this.estadoCargado || !this.el("formGenetico").reportValidity()) return;
    const datos = { poblacion: this.el("inputPoblacion").valueAsNumber, generaciones: this.el("inputGeneraciones").valueAsNumber, tasa_mutacion: this.el("inputTasaMutacion").valueAsNumber / 100, temperatura_fija: this.el("inputTempFijaBase").valueAsNumber };
    this.setOcupado(true);
    this.limpiarError();
    this.el("btnEjecutarGA").textContent = "Evolucionando…";
    this.el("gaProgressStatus").hidden = false;
    this.status(`Evolucionando reglas con AG · N = ${datos.poblacion}, G = ${datos.generaciones}…`, "busy");
    let completado = false;
    try {
      const data = await this.pedir("/api/optimizar-genetico", datos);
      this.optimizado = true;
      this.actualizarModelo(data);
      // La curva de salida anterior pertenece a otra tabla y deja de ser válida.
      this.salida = null;
      completado = true;
    } catch (error) { this.mostrarError(error.message); }
    finally {
      this.setOcupado(false);
      this.el("btnEjecutarGA").textContent = "▶ Evolucionar con AG";
      this.el("gaProgressStatus").hidden = true;
    }
    if (completado) {
      await this.ejecutarInferencia();
      if (this.el("mensajeError").hidden) this.status("Optimización completada. Costo, consumo y reglas actualizados.");
    }
  },

  status(text, state = "ready") { this.el("statusText").textContent = text; this.el("statusDot").className = `status-dot ${state}`; },
  mostrarError(text) { this.el("textoError").textContent = text; this.el("mensajeError").hidden = false; this.status(text, "error"); },
  limpiarError() { this.el("mensajeError").hidden = true; },
  programarDibujo() {
    if (this.frame !== null) return;
    this.frame = requestAnimationFrame(() => { this.frame = null; this.dibujar(); });
  },
  dibujar() {
    if (!this.curvas || this.tab !== "tabFIS") return;
    if (this.detalle) {
      this.dibujarCurvas(this.el("canvasPertenencia"), this.curvas[this.variable], { variable: this.variable, axes: true, selected: this.conjunto });
    } else {
      Object.entries(this.variables).forEach(([key, variable]) => {
        if (variable.canvas) this.dibujarCurvas(this.el(variable.canvas), this.curvas[key], { variable: key, marker: this.entradasEvaluadas?.[key] });
      });
      const salida = this.salida?.curva_agregada;
      this.dibujarCurvas(this.el("canvasSalida"), salida?.x?.length ? { x: salida.x, conjuntos: { "Agregación": salida.y }, etiqueta_x: "Potencia de salida (%)" } : this.curvas.potencia_enfriamiento, { variable: "potencia_enfriamiento", axes: true, small: true, marker: this.salida?.potencia_enfriamiento, aggregate: Boolean(salida?.x?.length) });
      this.actualizarConectores();
    }
  },

  // Gráficas Canvas locales: los puntos y la salida agregada provienen de la API.
  dibujarCurvas(canvas, data, options = {}) {
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height || !data?.x?.length) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(rect.width * dpr); canvas.height = Math.round(rect.height * dpr);
    const ctx = canvas.getContext("2d"); ctx.scale(dpr, dpr);
    const w = rect.width, h = rect.height, axes = options.axes, small = options.small;
    const pad = axes ? { left: small ? 28 : 59, right: small ? 11 : 22, top: small ? 10 : 20, bottom: small ? 30 : 51 } : { left: 3, right: 3, top: 4, bottom: 4 };
    const plotW = w - pad.left - pad.right, plotH = h - pad.top - pad.bottom;
    const min = data.x[0], max = data.x.at(-1);
    const px = x => pad.left + (x - min) / (max - min) * plotW;
    const py = y => pad.top + (1 - y) * plotH;
    ctx.clearRect(0, 0, w, h);
    ctx.lineWidth = 1; ctx.font = `${small ? 8 : 11}px "Segoe UI", Arial, sans-serif`;
    if (axes) {
      ctx.strokeStyle = "#edf1f5";
      for (let i = 0; i <= 5; i++) {
        const y = py(i / 5); ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(w - pad.right, y); ctx.stroke();
        ctx.fillStyle = "#7d8b96"; ctx.textAlign = "right"; ctx.fillText((i / 5).toFixed(1), pad.left - 6, y + 3);
      }
      const tickStep = max - min <= 45 ? 5 : 20;
      for (let value = Math.ceil(min / tickStep) * tickStep; value <= max; value += tickStep) {
        const x = px(value); ctx.beginPath(); ctx.moveTo(x, pad.top); ctx.lineTo(x, py(0)); ctx.stroke();
        ctx.fillStyle = "#7d8b96"; ctx.textAlign = "center"; ctx.fillText(value, x, py(0) + (small ? 12 : 18));
      }
      ctx.fillStyle = "#647587"; ctx.textAlign = "center";
      ctx.fillText(data.etiqueta_x, pad.left + plotW / 2, h - (small ? 3 : 11));
      if (!small) { ctx.save(); ctx.translate(16, pad.top + plotH / 2); ctx.rotate(-Math.PI / 2); ctx.fillText("Grado de pertenencia (μ)", 0, 0); ctx.restore(); }
    }
    for (const [name, values] of Object.entries(data.conjuntos)) {
      const color = options.aggregate ? "#009ddb" : this.color(options.variable, name);
      const selected = name === options.selected;
      ctx.beginPath(); ctx.moveTo(px(min), py(0));
      data.x.forEach((x, index) => ctx.lineTo(px(x), py(values[index])));
      ctx.lineTo(px(max), py(0)); ctx.closePath(); ctx.fillStyle = color; ctx.globalAlpha = options.aggregate ? .18 : selected ? .13 : .06; ctx.fill();
      ctx.globalAlpha = 1; ctx.beginPath();
      data.x.forEach((x, index) => index ? ctx.lineTo(px(x), py(values[index])) : ctx.moveTo(px(x), py(values[index])));
      ctx.strokeStyle = color; ctx.lineWidth = selected ? 2 : 1.4; ctx.stroke();
    }
    ctx.strokeStyle = "#b8c8d4"; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(pad.left, py(0)); ctx.lineTo(w - pad.right, py(0)); ctx.stroke();
    if (Number.isFinite(options.marker)) {
      const x = px(Math.max(min, Math.min(max, options.marker)));
      ctx.setLineDash([3, 3]); ctx.strokeStyle = options.aggregate ? "#d5622a" : "#91a6b6";
      ctx.beginPath(); ctx.moveTo(x, pad.top); ctx.lineTo(x, py(0)); ctx.stroke(); ctx.setLineDash([]);
    }
  },
  actualizarConectores() {
    const area = this.el("fisCanvasArea").getBoundingClientRect();
    const center = this.el("blockMamdani").getBoundingClientRect();
    const startX = center.left - area.left, endX = center.right - area.left, centerY = center.top + center.height / 2 - area.top;
    ["blockInputRack", "blockInputCpu", "blockInputExt"].forEach((id, index) => {
      const block = this.el(id).getBoundingClientRect();
      const x = block.right - area.left, y = block.top + block.height / 2 - area.top, middle = (x + startX) / 2;
      this.el(`pathInput${index + 1}`).setAttribute("d", `M ${x} ${y} C ${middle} ${y}, ${middle} ${centerY}, ${startX - 2} ${centerY}`);
    });
    const out = this.el("blockOutputPotencia").getBoundingClientRect();
    this.el("pathOutput").setAttribute("d", `M ${endX} ${centerY} L ${out.left - area.left - 2} ${out.top + out.height / 2 - area.top}`);
  }
};

app.init();
