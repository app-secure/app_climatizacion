/**
 * MATLAB Fuzzy Logic Designer & Genetic Algorithm Optimizer - Frontend Controller
 * Proyecto: Climatización de Datacenter bajo ASHRAE TC 9.9 Clase A1
 */

const app = {
  reglas: [],
  curvasPertenencia: null,
  simulacionActual: null,
  graficosChartJS: {},
  miniGraficosFIS: {},
  superficieCargada: false,
  debounceTimer: null,

  // Inicialización al cargar la aplicación
  async init() {
    this.enlazarEventos();
    await this.cargarEstadoInicial();
    await this.cargarCurvasPertenencia();
    this.actualizarConectoresSVG();
    this.ejecutarInferencia();
  },

  // Enlace de Eventos del DOM
  enlazarEventos() {
    // Pestañas del espacio de trabajo
    document.querySelectorAll(".center-tab").forEach(tab => {
      tab.addEventListener("click", () => {
        const targetId = tab.getAttribute("data-tab");
        this.activarTab(targetId);
      });
    });

    // Botón de ejecución del Algoritmo Genético
    const btnGA = document.getElementById("btnEjecutarGA");
    if (btnGA) {
      btnGA.addEventListener("click", () => this.ejecutarAlgoritmoGenetico());
    }

    // Sliders del Probador Manual
    ["sliderRack", "sliderCpu", "sliderExt"].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener("input", () => {
          this.actualizarEtiquetasSlidersManuales();
          clearTimeout(this.debounceTimer);
          this.debounceTimer = setTimeout(() => this.ejecutarInferencia(), 60);
        });
      }
    });

    // Botón manual de cálculo
    const btnCalc = document.getElementById("btnCalcularInferencia");
    if (btnCalc) {
      btnCalc.addEventListener("click", () => this.ejecutarInferencia());
    }

    // Filtro de reglas en la tabla
    const selectFiltro = document.getElementById("selectFiltroRack");
    if (selectFiltro) {
      selectFiltro.addEventListener("change", (e) => {
        this.renderizarTablaReglas(this.reglas, e.target.value);
      });
    }

    // Superficie 3D
    const sliderSurf = document.getElementById("sliderSurfaceExt");
    if (sliderSurf) {
      sliderSurf.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value).toFixed(1);
        document.getElementById("valSurfaceExt").textContent = `${val} °C`;
      });
      sliderSurf.addEventListener("change", () => this.cargarSuperficie3D());
    }
    const btnSurf = document.getElementById("btnActualizarSuperficie");
    if (btnSurf) {
      btnSurf.addEventListener("click", () => this.cargarSuperficie3D());
    }

    // Redibujar SVG connectors al redimensionar ventana
    window.addEventListener("resize", () => {
      this.actualizarConectoresSVG();
      if (document.getElementById("tabSimulacion").classList.contains("active")) {
        Plotly.Plots.resize("plotSimulacionTemperatura");
        Plotly.Plots.resize("plotSimulacionPotenciaClima");
      }
      if (document.getElementById("tabSuperficie").classList.contains("active")) {
        Plotly.Plots.resize("plotSuperficie3D");
      }
    });
  },

  // Cambio de pestañas
  activarTab(tabId) {
    document.querySelectorAll(".center-tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

    const tabHead = document.querySelector(`.center-tab[data-tab="${tabId}"]`);
    const tabPane = document.getElementById(tabId);

    if (tabHead && tabPane) {
      tabHead.classList.add("active");
      tabPane.classList.add("active");
    }

    if (tabId === "tabSimulacion") {
      setTimeout(() => {
        Plotly.Plots.resize("plotSimulacionTemperatura");
        Plotly.Plots.resize("plotSimulacionPotenciaClima");
      }, 50);
    } else if (tabId === "tabFIS") {
      setTimeout(() => this.actualizarConectoresSVG(), 50);
    } else if (tabId === "tabSuperficie") {
      if (!this.superficieCargada) {
        this.cargarSuperficie3D();
      } else {
        setTimeout(() => Plotly.Plots.resize("plotSuperficie3D"), 50);
      }
    }
  },

  // Cargar estado inicial del sistema desde /api/estado
  async cargarEstadoInicial() {
    try {
      this.actualizarStatus("Cargando estado inicial del sistema...", true);
      const res = await fetch("/api/estado");
      const data = await res.json();

      this.reglas = data.reglas || [];
      this.simulacionActual = data;

      // Actualizar tabla de reglas
      this.renderizarTablaReglas(this.reglas, "TODOS");
      const badgeCount = document.getElementById("lblTotalReglasCount");
      if (badgeCount) badgeCount.textContent = `${this.reglas.length} Reglas Activas`;

      // Actualizar tarjetas de KPIs
      if (data.kpis) {
        this.actualizarTarjetasKPI(data.kpis);
      }

      // Renderizar gráficas de simulación de 96 pasos
      this.renderizarSimulacionPlotly(data);

      this.actualizarStatus("Sistema inicializado. 36 reglas activas cargadas en el controlador Mamdani.", false);
    } catch (err) {
      console.error("Error al cargar estado inicial:", err);
      this.actualizarStatus("Error de conexión con el servidor Flask.", false);
    }
  },

  // Actualizar Tarjetas de KPIs en el Sidebar Izquierdo
  actualizarTarjetasKPI(kpis) {
    if (!kpis) return;

    // Costo Diario AG
    const elCosto = document.getElementById("kpiCostoDiario");
    if (elCosto && kpis.costo_diario !== undefined) {
      elCosto.textContent = `$ ${Number(kpis.costo_diario).toFixed(2)} USD/día`;
    }

    // Porcentaje de ahorro
    const elAhorroPct = document.getElementById("kpiAhorroPct");
    const elAhorroUsd = document.getElementById("kpiAhorroDiarioUsd");
    const pct = kpis.ahorro_porcentaje !== undefined ? kpis.ahorro_porcentaje : (kpis.porcentaje_ahorro || 0);
    const ahorroUsd = kpis.ahorro_diario !== undefined ? kpis.ahorro_diario : 0;

    if (elAhorroPct) {
      if (pct >= 0) {
        elAhorroPct.className = "kpi-badge badge-green";
        elAhorroPct.textContent = `+${Number(pct).toFixed(1)} % Ahorro`;
      } else {
        elAhorroPct.className = "kpi-badge badge-blue";
        elAhorroPct.textContent = `${Number(pct).toFixed(1)} % Ahorro`;
      }
    }
    if (elAhorroUsd) {
      elAhorroUsd.textContent = `Ahorro: $ ${Math.abs(ahorroUsd).toFixed(2)} USD/día`;
    }

    // Consumo kWh
    const elConsumo = document.getElementById("kpiConsumoKwh");
    const elConsumoMes = document.getElementById("kpiConsumoMesKwh");
    if (elConsumo && kpis.consumo_kwh !== undefined) {
      elConsumo.textContent = `${Number(kpis.consumo_kwh).toFixed(1)} kWh`;
      if (elConsumoMes) {
        elConsumoMes.textContent = `~${Math.round(kpis.consumo_kwh * 30).toLocaleString()} kWh/mes`;
      }
    }

    // Temperaturas
    const elMax = document.getElementById("kpiTempMax");
    const elProm = document.getElementById("kpiTempProm");
    if (elMax && kpis.temp_maxima !== undefined) {
      elMax.textContent = `${Number(kpis.temp_maxima).toFixed(2)} °C`;
    }
    if (elProm && kpis.temp_promedio !== undefined) {
      elProm.textContent = `${Number(kpis.temp_promedio).toFixed(2)} °C`;
    }

    // Violaciones de Monotonía
    const elViol = document.getElementById("kpiViolaciones");
    if (elViol) {
      const v = kpis.violaciones_monotonia || 0;
      elViol.textContent = v;
      elViol.style.color = v === 0 ? "#16a34a" : "#dc2626";
    }
  },

  // Renderizar la simulación en lazo cerrado de 96 pasos (Plotly)
  renderizarSimulacionPlotly(data) {
    if (!data || !data.horas || !data.serie_temperaturas) return;

    const horas = data.horas;
    const tempAG = data.serie_temperaturas;
    const tempTermostato = data.serie_temperaturas_estandar || [];
    const potAG = data.serie_potencias;
    const potTermostato = data.serie_potencias_estandar || [];
    const tempExt = data.serie_temp_exterior || [];
    const cpu = data.serie_uso_cpu || [];

    // --- GRÁFICO 1: EVOLUCIÓN TÉRMICA DEL RACK (AG vs. TERMOSTATO vs. ASHRAE) ---
    const trazasTemp = [
      // Banda sombreada ASHRAE (18 a 27 °C)
      {
        x: [horas[0], horas[horas.length - 1], horas[horas.length - 1], horas[0]],
        y: [18.0, 18.0, 27.0, 27.0],
        fill: "toself",
        fillcolor: "rgba(16, 185, 129, 0.08)",
        line: { color: "transparent" },
        showlegend: false,
        hoverinfo: "none",
        name: "Banda Óptima ASHRAE"
      },
      // Límite ASHRAE 27 °C
      {
        x: [horas[0], horas[horas.length - 1]],
        y: [27.0, 27.0],
        mode: "lines",
        name: "Límite ASHRAE (27 °C)",
        line: { color: "#f59e0b", width: 1.8, dash: "dot" }
      },
      // Límite Dell R740 30 °C
      {
        x: [horas[0], horas[horas.length - 1]],
        y: [30.0, 30.0],
        mode: "lines",
        name: "Límite Crítico Dell (30 °C)",
        line: { color: "#ef4444", width: 1.5, dash: "dash" }
      },
      // Línea Base: Termostato 18 °C
      {
        x: horas,
        y: tempTermostato,
        mode: "lines",
        name: "Termostato Proporcional 18 °C",
        line: { color: "#64748b", width: 2, dash: "dash" }
      },
      // Controlador Difuso Evolucionado (AG)
      {
        x: horas,
        y: tempAG,
        mode: "lines",
        name: "Controlador Difuso (AG)",
        line: { color: "#0284c7", width: 2.8 }
      }
    ];

    const layoutTemp = {
      margin: { l: 50, r: 25, t: 25, b: 35 },
      xaxis: {
        title: { text: "Hora del Día (h)", font: { size: 10.5, color: "#334155" } },
        tickvals: [0, 3, 6, 9, 12, 15, 18, 21, 24],
        gridcolor: "#f1f5f9",
        zeroline: false
      },
      yaxis: {
        title: { text: "Temp. Rack (°C)", font: { size: 10.5, color: "#334155" } },
        range: [15, 32],
        gridcolor: "#f1f5f9"
      },
      legend: {
        orientation: "h",
        y: 1.15,
        x: 0,
        font: { size: 10 }
      },
      hovermode: "x unified",
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff"
    };

    Plotly.react("plotSimulacionTemperatura", trazasTemp, layoutTemp, { responsive: true, displayModeBar: false });

    // --- GRÁFICO 2: DINÁMICA DE POTENCIA HVAC Y CLIMA EXTERIOR ---
    const trazasPot = [
      // Potencia AG
      {
        x: horas,
        y: potAG,
        mode: "lines",
        name: "Potencia HVAC AG (%)",
        fill: "tozeroy",
        fillcolor: "rgba(2, 132, 199, 0.18)",
        line: { color: "#0284c7", width: 2.2 }
      },
      // Potencia Termostato
      {
        x: horas,
        y: potTermostato,
        mode: "lines",
        name: "Potencia Termostato 18 °C (%)",
        line: { color: "#94a3b8", width: 1.8, dash: "dot" }
      },
      // Carga CPU
      {
        x: horas,
        y: cpu,
        mode: "lines",
        name: "Carga CPU Servidores (%)",
        line: { color: "#8b5cf6", width: 1.5 }
      },
      // Temperatura Exterior (Eje secundario)
      {
        x: horas,
        y: tempExt,
        mode: "lines",
        name: "Temp. Exterior (°C)",
        yaxis: "y2",
        line: { color: "#ea580c", width: 2 }
      }
    ];

    const layoutPot = {
      margin: { l: 50, r: 50, t: 25, b: 35 },
      xaxis: {
        title: { text: "Hora del Día (h)", font: { size: 10.5, color: "#334155" } },
        tickvals: [0, 3, 6, 9, 12, 15, 18, 21, 24],
        gridcolor: "#f1f5f9",
        zeroline: false
      },
      yaxis: {
        title: { text: "Potencia / CPU (%)", font: { size: 10.5, color: "#334155" } },
        range: [0, 105],
        gridcolor: "#f1f5f9"
      },
      yaxis2: {
        title: { text: "Temp. Exterior (°C)", font: { size: 10.5, color: "#ea580c" } },
        range: [5, 42],
        overlaying: "y",
        side: "right",
        gridcolor: "transparent"
      },
      legend: {
        orientation: "h",
        y: 1.15,
        x: 0,
        font: { size: 10 }
      },
      hovermode: "x unified",
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff"
    };

    Plotly.react("plotSimulacionPotenciaClima", trazasPot, layoutPot, { responsive: true, displayModeBar: false });
  },

  // Renderizar la tabla de 36 reglas (Sin aptitud individual por regla)
  renderizarTablaReglas(reglas, filtroRack = "TODOS") {
    const tbody = document.getElementById("tbodyReglas36");
    if (!tbody) return;
    tbody.innerHTML = "";

    const reglasFiltradas = reglas.filter(r => {
      if (filtroRack === "TODOS") return true;
      const ant = r.antecedentes || {};
      return ant.temperatura_rack === filtroRack;
    });

    reglasFiltradas.forEach(r => {
      const tr = document.createElement("tr");
      const id = r.identificador || r.id;
      const ant = r.antecedentes || {};
      const rack = ant.temperatura_rack || "--";
      const cpu = ant.uso_cpu || "--";
      const ext = ant.temperatura_exterior || "--";
      const cons = r.etiqueta_consecuente || "N/A";
      const nivel = r.nivel !== undefined ? r.nivel : 0;

      // Colores de badges por antecedente
      const badgeRackClass = `badge-rack-${rack.toLowerCase()}`;
      const badgeConsClass = `badge-consecuente-${cons.toLowerCase()}`;

      tr.innerHTML = `
        <td style="text-align: center; font-weight: bold; color: #64748b;">${id}</td>
        <td>
          IF <span class="kpi-badge ${badgeRackClass}">${rack}</span>
          AND CPU <span class="kpi-badge badge-blue">${cpu}</span>
          AND T_ext <span class="kpi-badge badge-blue">${ext}</span>
        </td>
        <td style="text-align: center;">
          THEN <span class="kpi-badge ${badgeConsClass}">${cons}</span>
        </td>
        <td style="text-align: center;">
          <span class="badge-nivel">${nivel}</span>
        </td>
      `;
      tbody.appendChild(tr);
    });
  },

  // Carga y renderizado de las 4 funciones de pertenencia completas y mini-canvases FIS
  async cargarCurvasPertenencia() {
    try {
      const res = await fetch("/api/curvas-pertenencia");
      const datos = await res.json();
      this.curvasPertenencia = datos;

      this.dibujarMiniCurvasFIS(datos);
      this.dibujarCurvasCompletasChartJS(datos);
    } catch (err) {
      console.error("Error al cargar curvas de pertenencia:", err);
    }
  },

  // Dibujar mini curvas en los bloques del diagrama FIS
  dibujarMiniCurvasFIS(datos) {
    const mapeo = {
      temperatura_rack: "miniCanvasRack",
      uso_cpu: "miniCanvasCpu",
      temperatura_exterior: "miniCanvasExt",
      potencia_enfriamiento: "miniCanvasPotencia"
    };

    const colores = {
      temperatura_rack: ["#0284c7", "#16a34a", "#eab308", "#dc2626"],
      uso_cpu: ["#0284c7", "#f59e0b", "#dc2626"],
      temperatura_exterior: ["#0284c7", "#f59e0b", "#dc2626"],
      potencia_enfriamiento: ["#16a34a", "#0284c7", "#f59e0b", "#dc2626"]
    };

    for (const [varKey, canvasId] of Object.entries(mapeo)) {
      const canvas = document.getElementById(canvasId);
      if (!canvas || !datos[varKey]) continue;

      const varData = datos[varKey];
      const ctx = canvas.getContext("2d");
      const datasets = [];
      let cIdx = 0;

      for (const [mfName, mfValues] of Object.entries(varData.conjuntos)) {
        const c = colores[varKey][cIdx % colores[varKey].length];
        datasets.push({
          label: mfName,
          data: mfValues.map((y, i) => ({ x: varData.x[i], y })),
          borderColor: c,
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
          tension: 0
        });
        cIdx++;
      }

      if (this.miniGraficosFIS[varKey]) {
        this.miniGraficosFIS[varKey].destroy();
      }

      this.miniGraficosFIS[varKey] = new Chart(ctx, {
        type: "line",
        data: { datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          scales: {
            x: { display: false },
            y: { display: false, min: 0, max: 1.05 }
          }
        }
      });
    }
  },

  // Dibujar gráficas de pertenencia de alta resolución para la inspección
  dibujarCurvasCompletasChartJS(datos) {
    const mapeo = {
      temperatura_rack: "chartFullRack",
      uso_cpu: "chartFullCpu",
      temperatura_exterior: "chartFullExt",
      potencia_enfriamiento: "chartFullPotencia"
    };

    const colores = {
      temperatura_rack: ["#0284c7", "#16a34a", "#f59e0b", "#dc2626"],
      uso_cpu: ["#0284c7", "#f59e0b", "#dc2626"],
      temperatura_exterior: ["#0284c7", "#f59e0b", "#dc2626"],
      potencia_enfriamiento: ["#16a34a", "#0284c7", "#f59e0b", "#dc2626"]
    };

    for (const [varKey, canvasId] of Object.entries(mapeo)) {
      const canvas = document.getElementById(canvasId);
      if (!canvas || !datos[varKey]) continue;

      const varData = datos[varKey];
      const ctx = canvas.getContext("2d");
      const datasets = [];
      let cIdx = 0;

      for (const [mfName, mfValues] of Object.entries(varData.conjuntos)) {
        const c = colores[varKey][cIdx % colores[varKey].length];
        datasets.push({
          label: mfName,
          data: mfValues.map((y, i) => ({ x: varData.x[i], y })),
          borderColor: c,
          backgroundColor: c + "18",
          borderWidth: 2,
          fill: true,
          pointRadius: 0,
          tension: 0
        });
        cIdx++;
      }

      if (this.graficosChartJS[varKey]) {
        this.graficosChartJS[varKey].destroy();
      }

      this.graficosChartJS[varKey] = new Chart(ctx, {
        type: "line",
        data: { datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          scales: {
            x: {
              type: "linear",
              title: { display: true, text: varData.etiqueta_x, font: { size: 9.5 } },
              grid: { color: "#f1f5f9" }
            },
            y: {
              min: 0,
              max: 1.05,
              title: { display: true, text: "μ", font: { size: 9.5 } },
              grid: { color: "#f1f5f9" }
            }
          },
          plugins: {
            legend: {
              position: "top",
              labels: { boxWidth: 10, font: { size: 9 } }
            }
          }
        }
      });
    }
  },

  // Actualizar los cables SVG de conexión en el Diagrama FIS
  actualizarConectoresSVG() {
    const area = document.getElementById("fisCanvasArea");
    if (!area) return;

    const b1 = document.getElementById("blockInputRack");
    const b2 = document.getElementById("blockInputCpu");
    const b3 = document.getElementById("blockInputExt");
    const center = document.querySelector(".fis-center-block");
    const out = document.getElementById("blockOutputPotencia");

    if (!b1 || !b2 || !b3 || !center || !out) return;

    const rectArea = area.getBoundingClientRect();
    const r1 = b1.getBoundingClientRect();
    const r2 = b2.getBoundingClientRect();
    const r3 = b3.getBoundingClientRect();
    const rc = center.getBoundingClientRect();
    const ro = out.getBoundingClientRect();

    const x1 = r1.right - rectArea.left;
    const y1 = r1.top + r1.height / 2 - rectArea.top;

    const x2 = r2.right - rectArea.left;
    const y2 = r2.top + r2.height / 2 - rectArea.top;

    const x3 = r3.right - rectArea.left;
    const y3 = r3.top + r3.height / 2 - rectArea.top;

    const xc_in = rc.left - rectArea.left;
    const yc = rc.top + rc.height / 2 - rectArea.top;

    const xc_out = rc.right - rectArea.left;
    const xo_in = ro.left - rectArea.left;
    const yo = ro.top + ro.height / 2 - rectArea.top;

    const p1 = document.getElementById("pathInput1");
    const p2 = document.getElementById("pathInput2");
    const p3 = document.getElementById("pathInput3");
    const pout = document.getElementById("pathOutput");

    if (p1) p1.setAttribute("d", `M ${x1} ${y1} C ${(x1 + xc_in) / 2} ${y1}, ${(x1 + xc_in) / 2} ${yc}, ${xc_in} ${yc}`);
    if (p2) p2.setAttribute("d", `M ${x2} ${y2} L ${xc_in} ${yc}`);
    if (p3) p3.setAttribute("d", `M ${x3} ${y3} C ${(x3 + xc_in) / 2} ${y3}, ${(x3 + xc_in) / 2} ${yc}, ${xc_in} ${yc}`);
    if (pout) pout.setAttribute("d", `M ${xc_out} ${yc} L ${xo_in} ${yo}`);
  },

  // Actualizar etiquetas numéricas al deslizar sliders manuales
  actualizarEtiquetasSlidersManuales() {
    const r = parseFloat(document.getElementById("sliderRack").value).toFixed(1);
    const c = parseFloat(document.getElementById("sliderCpu").value).toFixed(1);
    const e = parseFloat(document.getElementById("sliderExt").value).toFixed(1);

    document.getElementById("lblSliderRack").textContent = `${r} °C`;
    document.getElementById("lblSliderCpu").textContent = `${c} %`;
    document.getElementById("lblSliderExt").textContent = `${e} °C`;
  },

  // Ejecución de Inferencia Manual Rápida
  async ejecutarInferencia() {
    const tempRack = parseFloat(document.getElementById("sliderRack").value);
    const usoCpu = parseFloat(document.getElementById("sliderCpu").value);
    const tempExt = parseFloat(document.getElementById("sliderExt").value);

    try {
      const res = await fetch("/api/inferencia", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          temperatura_rack: tempRack,
          uso_cpu: usoCpu,
          temperatura_exterior: tempExt
        })
      });
      const data = await res.json();
      const z = Number(data.potencia_enfriamiento).toFixed(1);

      // Actualizar tarjeta del sidebar
      const elVal = document.getElementById("valPotenciaZ");
      const elBar = document.getElementById("meterPotenciaFill");
      const elLbl = document.getElementById("lblNivelConsecuente");

      if (elVal) elVal.textContent = `${z} %`;
      if (elBar) elBar.style.width = `${Math.min(100, Math.max(0, z))}%`;

      // Nivel consecuente
      let nivelNombre = "MEDIA";
      if (z <= 25.0) nivelNombre = "MINIMA";
      else if (z <= 55.0) nivelNombre = "MEDIA";
      else if (z <= 80.0) nivelNombre = "ALTA";
      else nivelNombre = "MAXIMA";

      if (elLbl) elLbl.textContent = nivelNombre;

      // Actualizar en el diagrama FIS
      const fisVal = document.getElementById("fisOutputValCentroid");
      if (fisVal) fisVal.textContent = `z* = ${z} % (${nivelNombre})`;
    } catch (err) {
      console.error("Error al calcular inferencia manual:", err);
    }
  },

  // Ejecutar el Algoritmo Genético
  async ejecutarAlgoritmoGenetico() {
    const poblacion = parseInt(document.getElementById("inputPoblacion").value) || 20;
    const generaciones = parseInt(document.getElementById("inputGeneraciones").value) || 20;
    const mutacionPct = parseFloat(document.getElementById("inputTasaMutacion").value) || 20;
    const tempFija = parseFloat(document.getElementById("inputTempFijaBase").value) || 18.0;

    const btn = document.getElementById("btnEjecutarGA");
    const loader = document.getElementById("gaProgressStatus");

    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Optimizando con AG...`;
    if (loader) loader.style.display = "block";
    this.actualizarStatus(`Evolucionando reglas con AG (N=${poblacion}, G=${generaciones}, Mut=${mutacionPct}%)...`, true);

    try {
      const res = await fetch("/api/optimizar-genetico", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          poblacion: poblacion,
          generaciones: generaciones,
          tasa_mutacion: mutacionPct / 100.0,
          temperatura_fija: tempFija
        })
      });
      const data = await res.json();

      // 1. Actualizar tarjetas de KPIs
      if (data.kpis) {
        this.actualizarTarjetasKPI(data.kpis);
      }

      // 2. Redibujar gráficas de simulación de 96 pasos con la mejor tabla obtenida
      this.simulacionActual = data;
      this.renderizarSimulacionPlotly(data);

      // 3. Actualizar la tabla de 36 reglas
      if (data.reglas && data.reglas.length > 0) {
        this.reglas = data.reglas;
        const filtro = document.getElementById("selectFiltroRack")?.value || "TODOS";
        this.renderizarTablaReglas(this.reglas, filtro);
      }

      // 4. Si la pestaña de superficie 3D está activa, recalcularla
      this.superficieCargada = false;
      if (document.getElementById("tabSuperficie").classList.contains("active")) {
        this.cargarSuperficie3D();
      }

      // 5. Reevaluar inferencia manual
      this.ejecutarInferencia();

      this.actualizarStatus("Optimización genética completada con éxito. Reglas activas sincronizadas.", false);
    } catch (err) {
      console.error("Error al ejecutar algoritmo genético:", err);
      this.actualizarStatus("Error durante la optimización genética.", false);
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-play"></i> Evolucionar Reglas con AG`;
      if (loader) loader.style.display = "none";
    }
  },

  // Cargar Superficie 3D con Plotly
  async cargarSuperficie3D() {
    const tempExt = parseFloat(document.getElementById("sliderSurfaceExt").value) || 20.0;
    this.actualizarStatus(`Calculando superficie 3D para Temp Ext = ${tempExt.toFixed(1)} °C...`, true);

    try {
      const res = await fetch(`/api/superficie-3d?temp_ext=${tempExt}`);
      const data = await res.json();

      const trace = {
        z: data.z,
        x: data.x,
        y: data.y,
        type: "surface",
        colorscale: "Viridis",
        hovertemplate: "Temp. Rack: %{x:.1f} °C<br>Uso CPU: %{y:.1f} %<br>Potencia HVAC: %{z:.1f} %<extra></extra>",
        contours: {
          z: { show: true, usecolormap: true, highlightcolor: "#38bdf8", project: { z: false } }
        }
      };

      const layout = {
        scene: {
          xaxis: { title: { text: "Temp. Rack (°C)", font: { size: 11, color: "#1e293b" } } },
          yaxis: { title: { text: "Uso CPU (%)", font: { size: 11, color: "#1e293b" } } },
          zaxis: { title: { text: "Potencia HVAC (%)", font: { size: 11, color: "#1e293b" } } },
          camera: { eye: { x: 1.7, y: -1.6, z: 1.2 } }
        },
        margin: { l: 20, r: 20, b: 20, t: 20 },
        paper_bgcolor: "#ffffff"
      };

      Plotly.newPlot("plotSuperficie3D", [trace], layout, { responsive: true, displayModeBar: false });
      this.superficieCargada = true;
      this.actualizarStatus("Superficie 3D calculada exitosamente.", false);
    } catch (err) {
      console.error("Error al cargar superficie 3D:", err);
      this.actualizarStatus("Error calculando superficie 3D.", false);
    }
  },

  // Barra de estado inferior
  actualizarStatus(msg, cargando = false) {
    const el = document.getElementById("statusbarText");
    const dot = document.getElementById("statusDot");
    if (el) el.textContent = msg;
    if (dot) dot.style.backgroundColor = cargando ? "#f59e0b" : "#10b981";
  }
};

// Iniciar aplicación al cargar el DOM
window.addEventListener("DOMContentLoaded", () => {
  app.init();
});
