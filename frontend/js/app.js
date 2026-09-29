/**
 * MATLAB Fuzzy Logic Designer - Lógica del Frontend
 * Integración con Backend: Algoritmo Genético (100 Casillas) y Control Difuso (Mamdani)
 */

const app = {
  reglas: [],
  reglaSeleccionada: null,
  graficosMF: {},
  miniGraficosFIS: {},
  graficoAgregacion: null,
  superficieCargada: false,
  debounceTimer: null,
  entradasActuales: { temperatura_rack: 22.0, uso_cpu: 50.0, temperatura_exterior: 20.0 },

  coordenadasMF: {},

  // Inicialización
  async init() {
    this.enlazarEventos();
    await this.cargarEstadoInicial();
    await this.cargarCoordenadasMF();
    await this.cargarCurvasPertenencia();
    this.ejecutarInferencia();
    setTimeout(() => this.dibujarConectoresFIS(), 100);
    window.addEventListener("resize", () => {
      const tabFIS = document.getElementById("tabFIS");
      if (tabFIS && tabFIS.classList.contains("active")) {
        this.dibujarConectoresFIS();
      }
    });
  },

  // Enlace de Eventos del DOM
  enlazarEventos() {
    // Tabs de la barra central (Reglas, Pertenencia, Superficie, Genético)
    document.querySelectorAll(".center-tab").forEach(tab => {
      tab.addEventListener("click", () => {
        const targetTabId = tab.getAttribute("data-tab");
        this.activarTab(targetTabId);
      });
    });

    // Evolucionar Base de Reglas con Algoritmo Genético
    const btnEvolucionar = document.getElementById("btnEvolucionarReglasToolbar");
    if (btnEvolucionar) {
      btnEvolucionar.addEventListener("click", () => this.evolucionarReglasGenetico());
    }

    // Limpiar Base de Reglas (volver al estado previo a reglas)
    const btnLimpiar = document.getElementById("btnLimpiarReglas");
    if (btnLimpiar) {
      btnLimpiar.addEventListener("click", () => this.limpiarReglas());
    }

    // Cambio de operador lógico de antecedentes (AND / OR)
    const selOperador = document.getElementById("selectOperadorReglas");
    if (selOperador) {
      selOperador.addEventListener("change", () => {
        const op = selOperador.value;
        const lblOp = document.getElementById("fisOperatorLabel");
        if (lblOp) {
          lblOp.textContent = op === "OR" ? "Or: Max" : "And: Min";
        }
        if (this.reglas && this.reglas.length > 0) {
          this.reglas.forEach(r => {
            if (op === "OR") {
              r.texto_regla = r.texto_regla.replace(/\bAND\b/g, "OR");
            } else {
              r.texto_regla = r.texto_regla.replace(/\bOR\b/g, "AND");
            }
          });
          this.renderizarTablaReglas(this.reglas);
        }
      });
    }

    // Editor de Coordenadas de Funciones de Pertenencia (Estilo MATLAB)
    const selVar = document.getElementById("selectMfVariable");
    const selConj = document.getElementById("selectMfConjunto");
    if (selVar && selConj) {
      selVar.addEventListener("change", () => this.alCambiarVariableMF());
      selConj.addEventListener("change", () => this.alCambiarConjuntoMF());
    }

    const btnAplicarMF = document.getElementById("btnAplicarCoordenadasMF");
    if (btnAplicarMF) {
      btnAplicarMF.addEventListener("click", () => this.guardarCoordenadasMFManual());
    }

    const btnResetMF = document.getElementById("btnRestablecerCoordenadasMF");
    if (btnResetMF) {
      btnResetMF.addEventListener("click", () => this.restablecerCoordenadasMFBase());
    }

    const selTipo = document.getElementById("selectMfTipo");
    if (selTipo) {
      selTipo.addEventListener("change", () => this.alCambiarTipoMF());
    }

    const inputParams = document.getElementById("inputMfParams");
    if (inputParams) {
      inputParams.addEventListener("input", () => this.alEditarTextoParams());
    }


    // Superficie 3D controles (Input numérico simple y botones de incremento/decremento)
    const inputSurf = document.getElementById("inputSurfaceExt");
    if (inputSurf) {
      inputSurf.addEventListener("change", () => {
        let val = parseFloat(inputSurf.value);
        if (isNaN(val)) val = 20.0;
        val = Math.max(0, Math.min(45, Math.round(val * 10) / 10));
        inputSurf.value = val.toFixed(1);
        this.cargarSuperficie3D(val);
      });
      inputSurf.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          inputSurf.dispatchEvent(new Event("change"));
        }
      });
    }

    const btnSubirSurf = document.getElementById("btnSubirTempExt");
    if (btnSubirSurf) {
      btnSubirSurf.addEventListener("click", () => {
        const inp = document.getElementById("inputSurfaceExt");
        if (inp) {
          let val = (parseFloat(inp.value) || 20.0) + 0.5;
          val = Math.min(45, Math.round(val * 10) / 10);
          inp.value = val.toFixed(1);
          this.cargarSuperficie3D(val);
        }
      });
    }

    const btnBajarSurf = document.getElementById("btnBajarTempExt");
    if (btnBajarSurf) {
      btnBajarSurf.addEventListener("click", () => {
        const inp = document.getElementById("inputSurfaceExt");
        if (inp) {
          let val = (parseFloat(inp.value) || 20.0) - 0.5;
          val = Math.max(0, Math.round(val * 10) / 10);
          inp.value = val.toFixed(1);
          this.cargarSuperficie3D(val);
        }
      });
    }

    const btnSurf = document.getElementById("btnActualizarSuperficie");
    if (btnSurf) {
      btnSurf.addEventListener("click", () => this.cargarSuperficie3D());
    }


    // Vector de Entradas en el Diagrama FIS [temp_rack, uso_cpu, temp_ext]
    const inputFis = document.getElementById("inputFisVector");
    if (inputFis) {
      inputFis.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          this.evaluarDesdeInputVector();
        }
      });
      inputFis.addEventListener("change", () => this.evaluarDesdeInputVector());
    }

    const btnEvalFis = document.getElementById("btnEjecutarInferenciaFis");
    if (btnEvalFis) {
      btnEvalFis.addEventListener("click", () => this.evaluarDesdeInputVector());
    }

    // Modal elegante: cerrar al hacer clic en el backdrop
    const modalSinReglas = document.getElementById("modalSinReglas");
    if (modalSinReglas) {
      modalSinReglas.addEventListener("click", (e) => {
        if (e.target === modalSinReglas) {
          this.cerrarModalSinReglas();
        }
      });
    }

  },

  // Cambiar pestaña activa y panel lateral dinámico
  activarTab(tabId) {
    document.querySelectorAll(".center-tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

    const tabHead = document.querySelector(`.center-tab[data-tab="${tabId}"]`);
    const tabPane = document.getElementById(tabId);

    if (tabHead && tabPane) {
      tabHead.classList.add("active");
      tabPane.classList.add("active");
    }

    // Alternar el panel lateral izquierdo dinámicamente según la pestaña activa
    document.querySelectorAll(".sidebar-panel").forEach(p => p.classList.remove("active"));
    if (tabId === "tabFIS" || tabId === "tabCurvas") {
      document.getElementById("sidebarPanelMF")?.classList.add("active");
    } else if (tabId === "tabReglas") {
      document.getElementById("sidebarPanelReglas")?.classList.add("active");
    } else if (tabId === "tabSuperficie") {
      document.getElementById("sidebarPanelSuperficie")?.classList.add("active");
      if (!this.superficieCargada) {
        this.cargarSuperficie3D();
      } else {
        setTimeout(() => {
          const plotEl = document.getElementById("plotSuperficie3D");
          if (plotEl && window.Plotly) {
            Plotly.Plots.resize(plotEl);
          }
        }, 80);
      }

    }

    if (tabId === "tabFIS") {
      setTimeout(() => {
        this.dibujarConectoresFIS();
        if (this.ultimosDatosCurvas) {
          this.renderizarMiniPlotsFIS(this.ultimosDatosCurvas);
          if (!this.reglas || this.reglas.length === 0) {
            this.renderizarCurvasPertenenciaSalida();
          }
        }
      }, 60);
    }

    // Al entrar al panel de curvas, mostrar la variable seleccionada actualmente en pantalla completa
    if (tabId === "tabCurvas") {
      const selVar = document.getElementById("selectMfVariable")?.value || "temperatura_rack";
      this.mostrarGraficoPertenencia(selVar);
    }
  },

  // Seleccionar variable desde el bloque interactivo del diagrama FIS
  seleccionarVariableDesdeFIS(nombreVariable) {
    const selVar = document.getElementById("selectMfVariable");
    if (selVar) {
      selVar.value = nombreVariable;
      this.alCambiarVariableMF();
    }
    this.mostrarGraficoPertenencia(nombreVariable);
  },

  // Mostrar el gráfico de la variable seleccionada en pantalla completa
  mostrarGraficoPertenencia(nombreVariable) {
    // Activar pestaña de curvas
    document.querySelectorAll(".center-tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
    const tabHead = document.querySelector(`.center-tab[data-tab="tabCurvas"]`);
    const tabPane = document.getElementById("tabCurvas");
    if (tabHead && tabPane) {
      tabHead.classList.add("active");
      tabPane.classList.add("active");
    }

    // Marcar tarjeta activa en el diagrama FIS y sincronizar editor MATLAB
    document.querySelectorAll(".fis-block-card").forEach(c => c.classList.remove("active"));
    const activeCard = document.getElementById(`fisCard-${nombreVariable}`);
    if (activeCard) activeCard.classList.add("active");

    const selVar = document.getElementById("selectMfVariable");
    if (selVar && selVar.value !== nombreVariable) {
      selVar.value = nombreVariable;
      this.alCambiarVariableMF();
    }

    // Mostrar únicamente la tarjeta de esta variable
    const cards = ["temperatura_rack", "uso_cpu", "temperatura_exterior", "potencia_enfriamiento"];
    cards.forEach(varKey => {
      const card = document.getElementById(`card-${varKey}`);
      if (card) {
        card.style.display = (varKey === nombreVariable) ? "flex" : "none";
      }
    });

    setTimeout(() => {
      if (this.graficosMF[nombreVariable]) {
        this.graficosMF[nombreVariable].resize();
      }
    }, 40);
  },

  // Cargar estado inicial del sistema desde Flask
  async cargarEstadoInicial() {
    try {
      this.actualizarStatus("Iniciando sistema de climatización bajo norma ASHRAE TC 9.9...", true);
      const res = await fetch("/api/estado");
      const data = await res.json();

      this.reglas = data.reglas || [];
      this.renderizarTablaReglas(this.reglas);
      const badgeReglas = document.getElementById("badgeReglasCount");
      if (badgeReglas) badgeReglas.textContent = this.reglas.length;

      const fisBadge = document.getElementById("fisRulesBadge");
      if (fisBadge) fisBadge.textContent = `${this.reglas.length} rules`;

      const badgeEstado = document.getElementById("badgeEstadoReglas");
      if (badgeEstado) {
        if (this.reglas.length > 0) {
          badgeEstado.textContent = "Estado: Óptimo (AG)";
          badgeEstado.style.background = "#dcfce7";
          badgeEstado.style.color = "#15803d";
        } else {
          badgeEstado.textContent = "Estado: Pendiente";
          badgeEstado.style.background = "#fef3c7";
          badgeEstado.style.color = "#b45309";
        }
      }

      this.actualizarStatus("Listo. Presione 'Evolucionar con AG' para generar el bloque óptimo de reglas difusas.", false);
    } catch (err) {
      console.error("Error al cargar estado inicial:", err);
      this.actualizarStatus("Error de conexión con el backend.", false);
    }
  },

  // Renderizar la tabla de reglas optimizadas
  renderizarTablaReglas(reglas) {
    const tbody = document.getElementById("tbodyReglas");
    tbody.innerHTML = "";

    if (!reglas || reglas.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="3" style="text-align: center; padding: 30px 20px; color: #64748b;">
            <div style="font-size: 24px; color: #0d9488; margin-bottom: 6px;"><i class="fa-solid fa-dna"></i></div>
            <div style="font-size: 13px; font-weight: 600; color: #334e68;">Base de Reglas Lista para Evolucionar</div>
            <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Presione 'Evolucionar con AG' en el panel izquierdo para generar las 36 reglas difusas óptimas</div>
          </td>
        </tr>`;
      return;
    }

    reglas.forEach((r, idx) => {
      const tr = document.createElement("tr");
      tr.id = `reglaRow_${idx}`;
      
      const confFormatted = (r.confianza || 0.95).toFixed(2);

      tr.innerHTML = `
        <td style="text-align: center; font-weight: bold; color: #57606a;">${idx + 1}</td>
        <td><code>${r.texto_regla}</code></td>
        <td style="text-align: center;"><span class="badge-weight">${confFormatted}</span></td>
      `;

      tr.addEventListener("click", () => this.seleccionarRegla(r, tr));
      tbody.appendChild(tr);
    });

    // Seleccionar la primera regla por defecto
    if (reglas.length > 0) {
      this.seleccionarRegla(reglas[0], tbody.firstElementChild);
    }
  },

  // Seleccionar regla y resaltarla en la tabla
  seleccionarRegla(regla, rowElement) {
    document.querySelectorAll("#tbodyReglas tr").forEach(tr => tr.classList.remove("selected"));
    if (rowElement) rowElement.classList.add("selected");
    this.reglaSeleccionada = regla;
  },

  // Parsear texto de vector de entradas "[22, 50, 20]"
  parsearVectorEntradas(str) {
    if (!str) return [22.0, 50.0, 20.0];
    const matches = str.match(/-?\d+(\.\d+)?/g);
    if (!matches || matches.length < 3) return null;
    return [parseFloat(matches[0]), parseFloat(matches[1]), parseFloat(matches[2])];
  },

  // Evaluar inferencia desde el campo de texto de entradas
  evaluarDesdeInputVector() {
    const inputEl = document.getElementById("inputFisVector");
    if (!inputEl) return;
    const valores = this.parsearVectorEntradas(inputEl.value);
    if (!valores || valores.length < 3) {
      alert("Por favor ingrese 3 valores numéricos para las entradas: [temperatura_rack, uso_cpu, temperatura_exterior]");
      return;
    }

    inputEl.value = `[${valores[0]}, ${valores[1]}, ${valores[2]}]`;
    this.entradasActuales = {
      temperatura_rack: valores[0],
      uso_cpu: valores[1],
      temperatura_exterior: valores[2]
    };

    this.ejecutarInferencia(true);
  },

  // Inferencia en Tiempo Real
  async ejecutarInferencia(origenUsuario = false) {
    // Si no hay reglas agregadas todavía, mostrar las funciones de pertenencia de potencia_enfriamiento
    if (!this.reglas || this.reglas.length === 0) {
      this.renderizarCurvasPertenenciaSalida();
      if (origenUsuario) {
        this.mostrarModalSinReglas();
      }
      return;
    }

    if (!this.entradasActuales) {
      const inputEl = document.getElementById("inputFisVector");
      const vals = this.parsearVectorEntradas(inputEl ? inputEl.value : "[22, 50, 20]") || [22.0, 50.0, 20.0];
      this.entradasActuales = {
        temperatura_rack: vals[0],
        uso_cpu: vals[1],
        temperatura_exterior: vals[2]
      };
    }

    const { temperatura_rack, uso_cpu, temperatura_exterior } = this.entradasActuales;

    try {
      const res = await fetch("/api/inferencia", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          temperatura_rack,
          uso_cpu,
          temperatura_exterior
        })
      });
      const data = await res.json();

      const potencia = data.potencia_enfriamiento.toFixed(1);
      const lblCent = document.getElementById("lblCentroideGrafico");
      if (lblCent) {
        lblCent.textContent = `z* = ${potencia} %`;
        lblCent.title = `Valor defuzzificado por centroide: ${potencia}%`;
      }

      // Renderizar gráfico de la figura difusa agregada y línea del centroide
      if (data.curva_agregada) {
        this.renderizarGraficoAgregacion(data.curva_agregada, parseFloat(potencia));
      }
    } catch (err) {
      console.error("Error en inferencia:", err);
    }
  },

  // Manejo de Modal Elegante sin Reglas
  mostrarModalSinReglas() {
    const modal = document.getElementById("modalSinReglas");
    if (modal) {
      modal.style.display = "flex";
    }
  },

  cerrarModalSinReglas() {
    const modal = document.getElementById("modalSinReglas");
    if (modal) {
      modal.style.display = "none";
    }
  },

  irAReglasDesdeModal() {
    this.cerrarModalSinReglas();
    this.activarTab("tabReglas");
    const btnEvolucionar = document.getElementById("btnEvolucionarReglasToolbar");
    if (btnEvolucionar) {
      btnEvolucionar.focus();
      btnEvolucionar.classList.add("pulse-highlight");
      setTimeout(() => btnEvolucionar.classList.remove("pulse-highlight"), 1800);
    }
  },

  // Renderizar funciones de pertenencia de potencia_enfriamiento cuando todavía no hay reglas
  renderizarCurvasPertenenciaSalida() {
    const canvas = document.getElementById("chartAgregacionDefuzz");
    if (!canvas) return;

    const lblCent = document.getElementById("lblCentroideGrafico");
    if (lblCent) {
      lblCent.textContent = "z* = -- %";
      lblCent.title = "Base sin reglas activas. Mostrando funciones de pertenencia de potencia_enfriamiento.";
    }

    if (!this.ultimosDatosCurvas || !this.ultimosDatosCurvas.potencia_enfriamiento) {
      return;
    }

    const varData = this.ultimosDatosCurvas.potencia_enfriamiento;
    const colores = {
      MINIMA: "#0284c7",  // Azul
      MEDIA:  "#10b981",  // Verde
      ALTA:   "#f59e0b",  // Ámbar
      MAXIMA: "#dc2626"   // Rojo
    };

    // Si ya existe un gráfico de funciones de pertenencia en este canvas, actualizarlo directamente
    if (this.graficoAgregacion) {
      if (this.graficoAgregacion.data.datasets.length === Object.keys(varData.conjuntos).length &&
          this.graficoAgregacion.data.datasets[0].label === "MINIMA") {
        Object.keys(varData.conjuntos).forEach((cName, idx) => {
          const vals = varData.conjuntos[cName];
          this.graficoAgregacion.data.datasets[idx].data = varData.x.map((xVal, i) => ({ x: xVal, y: vals[i] }));
        });
        this.graficoAgregacion.update("none");
        return;
      } else {
        this.graficoAgregacion.destroy();
        this.graficoAgregacion = null;
      }
    }

    const ctx = canvas.getContext("2d");
    const datasets = Object.keys(varData.conjuntos).map(cName => {
      const vals = varData.conjuntos[cName];
      const dataPoints = varData.x.map((xVal, i) => ({ x: xVal, y: vals[i] }));
      const color = colores[cName] || "#007acc";
      return {
        label: cName,
        data: dataPoints,
        borderColor: color,
        backgroundColor: color.replace(")", ", 0.08)").replace("rgb", "rgba"),
        borderWidth: 1.8,
        fill: false,
        tension: 0,
        pointRadius: 0
      };
    });

    this.graficoAgregacion = new Chart(ctx, {
      type: "line",
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        interaction: {
          mode: "index",
          intersect: false
        },
        scales: {
          x: {
            type: "linear",
            min: 0,
            max: 100,
            title: { display: true, text: "Potencia Enfriamiento (%)", font: { size: 9 } },
            ticks: { font: { size: 8 } },
            grid: { color: "#f1f5f9" }
          },
          y: {
            min: 0,
            max: 1.1,
            title: { display: true, text: "μ", font: { size: 9 } },
            ticks: { font: { size: 8 } },
            grid: { color: "#f1f5f9" }
          }
        },
        plugins: {
          legend: {
            display: true,
            position: "top",
            labels: {
              boxWidth: 8,
              boxHeight: 8,
              font: { size: 8.5 },
              padding: 4
            }
          },
          tooltip: {
            enabled: true,
            callbacks: {
              title: function(items) {
                if (!items || !items.length) return "";
                return `Potencia: ${items[0].parsed.x.toFixed(1)} %`;
              },
              label: function(item) {
                const muVal = item.parsed.y;
                return `  ● ${item.dataset.label}: μ = ${muVal.toFixed(3)}`;
              }
            }
          }
        }
      }
    });
  },

  // Renderizar gráfico de Agregación Difusa y Centroide en el panel derecho
  renderizarGraficoAgregacion(curvaAgregada, centroideVal) {
    const canvas = document.getElementById("chartAgregacionDefuzz");
    if (!canvas) return;

    const lblCentroide = document.getElementById("lblCentroideGrafico");
    if (lblCentroide) {
      lblCentroide.textContent = `z* = ${centroideVal.toFixed(1)} %`;
      lblCentroide.title = `Centroide defuzzificado z* = ${centroideVal.toFixed(1)}%`;
    }

    if (!curvaAgregada || !curvaAgregada.x || curvaAgregada.x.length === 0) return;

    const ctx = canvas.getContext("2d");
    const dataPoints = curvaAgregada.x.map((xVal, i) => ({ x: xVal, y: curvaAgregada.y[i] }));

    const lineaCentroide = [
      { x: centroideVal, y: 0 },
      { x: centroideVal, y: 1.05 }
    ];

    // Si el gráfico previo era de funciones de pertenencia (más de 2 datasets), destruirlo
    if (this.graficoAgregacion) {
      if (this.graficoAgregacion.data.datasets.length === 2 && this.graficoAgregacion.data.datasets[0].label === "Conjunto Agregado") {
        this.graficoAgregacion.data.datasets[0].data = dataPoints;
        this.graficoAgregacion.data.datasets[1].data = lineaCentroide;
        this.graficoAgregacion.update("none");
        return;
      } else {
        this.graficoAgregacion.destroy();
        this.graficoAgregacion = null;
      }
    }

    this.graficoAgregacion = new Chart(ctx, {
      type: "line",
      data: {
        datasets: [
          {
            label: "Conjunto Agregado",
            data: dataPoints,
            borderColor: "#007acc",
            backgroundColor: "rgba(0, 122, 204, 0.22)",
            borderWidth: 1.8,
            fill: true,
            tension: 0,
            pointRadius: 0
          },
          {
            label: "Centroide (z*)",
            data: lineaCentroide,
            borderColor: "#dc2626",
            borderWidth: 2,
            borderDash: [4, 4],
            fill: false,
            tension: 0,
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        interaction: {
          mode: "index",
          intersect: false
        },
        scales: {
          x: {
            type: "linear",
            min: 0,
            max: 100,
            title: { display: true, text: "Potencia Salida (%)", font: { size: 9 } },
            ticks: { font: { size: 8 } },
            grid: { color: "#f1f5f9" }
          },
          y: {
            min: 0,
            max: 1.1,
            title: { display: true, text: "μ", font: { size: 9 } },
            ticks: { font: { size: 8 } },
            grid: { color: "#f1f5f9" }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            enabled: true,
            callbacks: {
              title: function(items) {
                if (!items || !items.length) return "";
                return `Potencia: ${items[0].parsed.x.toFixed(1)} %`;
              },
              label: function(item) {
                if (item.datasetIndex === 1) {
                  return `  Centroide z* = ${centroideVal.toFixed(1)} %`;
                }
                return `  μ Agregado = ${item.parsed.y.toFixed(3)}`;
              }
            }
          }
        }
      }
    });
  },

  // Evolución de la Base de Reglas con Algoritmo Genético
  async evolucionarReglasGenetico() {
    const poblacion = parseInt(document.getElementById("gaPoblacionReglas")?.value) || 60;
    const generaciones = parseInt(document.getElementById("gaGeneracionesReglas")?.value) || 20;
    const mutacionPct = parseFloat(document.getElementById("gaMutacionReglas")?.value) || 15.0;
    const tasaMutacion = Math.max(0.01, Math.min(0.5, mutacionPct / 100.0));
    const operador = document.getElementById("selectOperadorReglas")?.value || "AND";

    const btn = document.getElementById("btnEvolucionarReglasToolbar");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Evolucionando con AG...`;
    }
    this.actualizarStatus(`Evolucionando bloque óptimo de reglas difusas con Operador ${operador} (Población: ${poblacion}, Gen: ${generaciones})...`, true);

    try {
      const res = await fetch("/api/evolucionar-reglas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          poblacion,
          generaciones,
          tasa_mutacion: tasaMutacion,
          operador: operador
        })
      });
      const data = await res.json();

      if (data.error) {
        alert(data.error);
        this.actualizarStatus(data.error, false);
        return;
      }

      this.reglas = data.reglas || [];
      this.renderizarTablaReglas(this.reglas);

      const badgeReglas = document.getElementById("badgeReglasCount");
      if (badgeReglas) badgeReglas.textContent = this.reglas.length;

      const badgeEstado = document.getElementById("badgeEstadoReglas");
      if (badgeEstado) {
        badgeEstado.textContent = `Estado: Óptimo (AG - ${operador})`;
        badgeEstado.style.background = "#dcfce7";
        badgeEstado.style.color = "#15803d";
      }

      const lblOp = document.getElementById("fisOperatorLabel");
      if (lblOp) {
        lblOp.textContent = operador === "OR" ? "Or: Max" : "And: Min";
      }

      const fisBadge = document.getElementById("fisRulesBadge");
      if (fisBadge) fisBadge.textContent = `${this.reglas.length} rules`;

      this.actualizarStatus(data.mensaje || `Base de 36 reglas evolucionada exitosamente con operador ${operador}.`, false);
      this.ejecutarInferencia(false);
    } catch (err) {
      console.error("Error al evolucionar reglas:", err);
      this.actualizarStatus("Error al ejecutar Algoritmo Genético para reglas.", false);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-dna"></i> Evolucionar con AG`;
      }
    }
  },

  // Limpiar base de reglas y restablecer salida a funciones de pertenencia
  async limpiarReglas() {
    try {
      this.actualizarStatus("Limpiando base de reglas difusas...", true);
      const res = await fetch("/api/limpiar-reglas", { method: "POST" });
      const data = await res.json();

      this.reglas = [];
      this.renderizarTablaReglas([]);

      const badgeReglas = document.getElementById("badgeReglasCount");
      if (badgeReglas) badgeReglas.textContent = "0";

      const badgeEstado = document.getElementById("badgeEstadoReglas");
      if (badgeEstado) {
        badgeEstado.textContent = "Estado: Pendiente";
        badgeEstado.style.background = "#fef3c7";
        badgeEstado.style.color = "#b45309";
      }

      const fisBadge = document.getElementById("fisRulesBadge");
      if (fisBadge) fisBadge.textContent = "0 rules";

      // Renderizar funciones de pertenencia en la salida
      this.renderizarCurvasPertenenciaSalida();
      this.actualizarStatus("Base de reglas limpiada. Mostrando funciones de pertenencia de potencia_enfriamiento.", false);
    } catch (err) {
      console.error("Error al limpiar reglas:", err);
      this.actualizarStatus("Error al limpiar reglas.", false);
    }
  },

  // Cargar coordenadas de los conjuntos difusos desde el backend
  async cargarCoordenadasMF() {
    try {
      const res = await fetch("/api/coordenadas-pertenencia");
      this.coordenadasMF = await res.json();
      this.alCambiarVariableMF();
    } catch (err) {
      console.error("Error al cargar coordenadas MF:", err);
    }
  },

  // Al seleccionar otra variable en el dropdown de MATLAB
  alCambiarVariableMF() {
    const varName = document.getElementById("selectMfVariable")?.value || "temperatura_rack";
    const selConj = document.getElementById("selectMfConjunto");
    if (!selConj || !this.coordenadasMF[varName]) return;

    selConj.innerHTML = "";
    Object.keys(this.coordenadasMF[varName]).forEach(cName => {
      const opt = document.createElement("option");
      opt.value = cName;
      opt.textContent = cName;
      selConj.appendChild(opt);
    });

    this.alCambiarConjuntoMF();

    const tabCurvas = document.getElementById("tabCurvas");
    if (tabCurvas && tabCurvas.classList.contains("active")) {
      this.mostrarGraficoPertenencia(varName);
    }
  },

  // Al seleccionar otro conjunto difuso (MF)
  alCambiarConjuntoMF() {
    const varName = document.getElementById("selectMfVariable")?.value;
    const conjName = document.getElementById("selectMfConjunto")?.value;
    if (!varName || !conjName || !this.coordenadasMF[varName] || !this.coordenadasMF[varName][conjName]) return;

    const conf = this.coordenadasMF[varName][conjName];
    const selTipo = document.getElementById("selectMfTipo");
    const inputParams = document.getElementById("inputMfParams");

    if (selTipo) selTipo.value = conf.tipo || "trapmf";
    if (inputParams) inputParams.value = conf.params.join(", ");

    // Generar campos numéricos dinámicos
    this.generarCamposDinamicosCoordenadas(conf.tipo || "trapmf", conf.params);
  },

  // Sincronizar texto [a, b, c, d] hacia la caja de texto al mover inputs individuales
  sincronizarTextoParamsDesdeCampos() {
    const container = document.getElementById("mfDynamicCoordsContainer");
    if (!container) return;
    const inputs = container.querySelectorAll(".mf-coord-input");
    const valores = Array.from(inputs).map(inp => parseFloat(inp.value) || 0.0);
    const inputTexto = document.getElementById("inputMfParams");
    if (inputTexto) {
      inputTexto.value = valores.join(", ");
    }
  },

  // Generar campos dinámicos individuales según el tipo matemático elegido (trapmf, trimf, gaussmf, sigmf, zmf, smf)
  generarCamposDinamicosCoordenadas(tipo, params = []) {
    const container = document.getElementById("mfDynamicCoordsContainer");
    if (!container) return;
    container.innerHTML = "";

    // Actualizar dinámicamente el label del vector según la función
    const vectorLabels = {
      trapmf: "Vector: [a, b, c, d]",
      trimf: "Vector: [a, b, c]",
      gaussmf: "Vector: [μ, σ]",
      sigmf: "Vector: [c, a]",
      zmf: "Vector: [a, b]",
      smf: "Vector: [a, b]"
    };
    const lblVector = document.getElementById("lblVectorParams");
    if (lblVector) {
      lblVector.textContent = vectorLabels[tipo] || "Vector: [a, b, c, d]";
    }

    const definiciones = {
      trapmf: [
        { label: "Inicio Base", default: 10.0 },
        { label: "Inicio Meseta", default: 14.0 },
        { label: "Fin Meseta", default: 20.0 },
        { label: "Fin Base", default: 25.0 }
      ],
      trimf: [
        { label: "Inicio Base", default: 15.0 },
        { label: "Vértice / Pico", default: 22.0 },
        { label: "Fin Base", default: 28.0 }
      ],
      gaussmf: [
        { label: "Centro / Media", default: 22.0 },
        { label: "Desviación Estándar", default: 3.5 }
      ],
      sigmf: [
        { label: "Punto de Inflexión", default: 22.0 },
        { label: "Pendiente", default: 2.0 }
      ],
      zmf: [
        { label: "Inicio Descenso", default: 16.0 },
        { label: "Fin Descenso", default: 22.0 }
      ],
      smf: [
        { label: "Inicio Ascenso", default: 22.0 },
        { label: "Fin Ascenso", default: 28.0 }
      ]
    };

    const defs = definiciones[tipo] || definiciones.trapmf;

    defs.forEach((d, idx) => {
      const val = (params[idx] !== undefined && !isNaN(params[idx])) ? params[idx] : d.default;
      const row = document.createElement("div");
      row.className = "mf-coord-row";
      row.innerHTML = `
        <label class="mf-coord-label" style="font-size: 11px; font-weight: 600; color: #334155;">${d.label}:</label>
        <input type="number" step="0.5" class="mf-coord-input" data-idx="${idx}" value="${val}">
      `;
      container.appendChild(row);

      const inputEl = row.querySelector("input");
      inputEl.addEventListener("input", () => {
        this.sincronizarTextoParamsDesdeCampos();
      });
    });

    const inputTexto = document.getElementById("inputMfParams");
    if (inputTexto) {
      const valores = Array.from(container.querySelectorAll(".mf-coord-input")).map(i => parseFloat(i.value) || 0.0);
      inputTexto.value = valores.join(", ");
    }
  },

  // Al cambiar el tipo de función de pertenencia en el dropdown
  alCambiarTipoMF() {
    const selTipo = document.getElementById("selectMfTipo");
    const tipo = selTipo ? selTipo.value : "trapmf";
    const inputTexto = document.getElementById("inputMfParams");
    let paramsActuales = [];
    if (inputTexto) {
      paramsActuales = inputTexto.value
        .replace(/[\[\]]/g, "")
        .split(/[,\s]+/)
        .map(p => parseFloat(p))
        .filter(p => !isNaN(p));
    }

    // Adaptar inteligentemente los parámetros al nuevo tipo
    let nuevosParams = [];
    if (tipo === "trapmf") {
      if (paramsActuales.length >= 4) {
        nuevosParams = paramsActuales.slice(0, 4);
      } else if (paramsActuales.length === 3) {
        const [a, b, c] = paramsActuales;
        nuevosParams = [a, (a + b) / 2, (b + c) / 2, c];
      } else if (paramsActuales.length === 2) {
        const [a, b] = paramsActuales;
        const diff = (b - a) / 3;
        nuevosParams = [a, a + diff, a + 2 * diff, b];
      } else {
        nuevosParams = [10.0, 15.0, 20.0, 25.0];
      }
    } else if (tipo === "trimf") {
      if (paramsActuales.length === 4) {
        const [a, b, c, d] = paramsActuales;
        nuevosParams = [a, (b + c) / 2, d];
      } else if (paramsActuales.length >= 3) {
        nuevosParams = paramsActuales.slice(0, 3);
      } else if (paramsActuales.length === 2) {
        const [a, b] = paramsActuales;
        nuevosParams = [a, (a + b) / 2, b];
      } else {
        nuevosParams = [15.0, 22.0, 28.0];
      }
    } else if (tipo === "gaussmf") {
      if (paramsActuales.length >= 3) {
        const minVal = paramsActuales[0];
        const maxVal = paramsActuales[paramsActuales.length - 1];
        const media = (minVal + maxVal) / 2;
        const sigma = Math.max(0.5, (maxVal - minVal) / 4);
        nuevosParams = [parseFloat(media.toFixed(1)), parseFloat(sigma.toFixed(1))];
      } else if (paramsActuales.length === 2) {
        nuevosParams = paramsActuales;
      } else {
        nuevosParams = [22.0, 3.5];
      }
    } else if (tipo === "sigmf") {
      if (paramsActuales.length >= 2) {
        nuevosParams = [paramsActuales[0], 2.0];
      } else {
        nuevosParams = [22.0, 2.0];
      }
    } else if (tipo === "zmf" || tipo === "smf") {
      if (paramsActuales.length >= 3) {
        nuevosParams = [paramsActuales[0], paramsActuales[paramsActuales.length - 1]];
      } else if (paramsActuales.length === 2) {
        nuevosParams = paramsActuales;
      } else {
        nuevosParams = [18.0, 26.0];
      }
    }

    this.generarCamposDinamicosCoordenadas(tipo, nuevosParams);
  },

  // Al editar directamente el campo de texto manual
  alEditarTextoParams() {
    const inputTexto = document.getElementById("inputMfParams");
    if (!inputTexto) return;
    const partes = inputTexto.value
      .replace(/[\[\]]/g, "")
      .split(/[,\s]+/)
      .map(p => parseFloat(p))
      .filter(p => !isNaN(p));

    const container = document.getElementById("mfDynamicCoordsContainer");
    if (!container) return;
    const inputs = container.querySelectorAll(".mf-coord-input");
    inputs.forEach((inp, i) => {
      if (partes[i] !== undefined) {
        inp.value = partes[i];
      }
    });
  },

  // Guardar coordenadas manuales editadas por el usuario estilo MATLAB
  async guardarCoordenadasMFManual() {
    const varName = document.getElementById("selectMfVariable")?.value;
    const conjName = document.getElementById("selectMfConjunto")?.value;
    const tipo = document.getElementById("selectMfTipo")?.value || "trapmf";
    const paramsRaw = document.getElementById("inputMfParams")?.value || "";

    // Parsear parámetros (soporta comas o espacios: [a, b, c, d] o a b c d)
    const params = paramsRaw
      .replace(/[\[\]]/g, "")
      .split(/[,\s]+/)
      .map(p => parseFloat(p))
      .filter(p => !isNaN(p));

    const paramsEsperados = {
      trapmf: 4,
      trimf: 3,
      gaussmf: 2,
      sigmf: 2,
      zmf: 2,
      smf: 2
    };

    const numReq = paramsEsperados[tipo] || 4;
    if (params.length !== numReq) {
      alert(`Para la función '${tipo}' se requieren exactamente ${numReq} parámetros. Coordenadas ingresadas: ${params.length}`);
      return;
    }

    if (tipo === "trapmf" && !(params[0] <= params[1] && params[1] <= params[2] && params[2] <= params[3])) {
      alert("En 'trapmf' debe cumplirse el orden matemático: a <= b <= c <= d.");
      return;
    }
    if (tipo === "trimf" && !(params[0] <= params[1] && params[1] <= params[2])) {
      alert("En 'trimf' debe cumplirse el orden matemático: a <= b <= c.");
      return;
    }
    if (tipo === "gaussmf" && params[1] <= 0) {
      alert("En 'gaussmf' la desviación estándar (σ) debe ser mayor que cero.");
      return;
    }
    if ((tipo === "zmf" || tipo === "smf") && params[0] >= params[1]) {
      alert(`En '${tipo}' el inicio (a) debe ser menor que el fin (b).`);
      return;
    }

    const btn = document.getElementById("btnAplicarCoordenadasMF");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Guardando...`;
    }

    this.actualizarStatus(`Actualizando coordenadas de '${varName}.${conjName}' a [${params.join(", ")}]...`, true);

    try {
      const res = await fetch("/api/actualizar-coordenadas-mf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          variable: varName,
          conjunto: conjName,
          tipo: tipo,
          params: params
        })
      });
      const data = await res.json();

      if (data.error) {
        alert(data.error);
        this.actualizarStatus(data.error, false);
        return;
      }

      this.coordenadasMF = data.todas_coordenadas || this.coordenadasMF;
      this.alCambiarConjuntoMF();

      // Destruir y redibujar gráficos con las nuevas formas exactas
      Object.values(this.graficosMF).forEach(g => g?.destroy());
      this.graficosMF = {};
      await this.cargarCurvasPertenencia();

      // Recalcular inferencia en vivo con el centroide
      this.ejecutarInferencia();
      this.superficieCargada = false;

      this.actualizarStatus(data.mensaje || `Coordenadas actualizadas exitosamente.`, false);
    } catch (err) {
      console.error("Error al guardar coordenadas MF:", err);
      this.actualizarStatus("Error al actualizar coordenadas.", false);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-check"></i> Aplicar Coordenadas`;
      }
    }
  },

  // Restablecer valores de fábrica ASHRAE / Dell
  async restablecerCoordenadasMFBase() {
    if (!confirm("¿Desea restablecer todas las coordenadas a los valores recomendados por ASHRAE TC 9.9 y Dell R740?")) {
      return;
    }

    this.actualizarStatus("Restableciendo funciones de pertenencia a valores estándar...", true);
    try {
      const res = await fetch("/api/restablecer-coordenadas-mf", { method: "POST" });
      const data = await res.json();

      this.coordenadasMF = data.todas_coordenadas || {};
      this.alCambiarVariableMF();

      Object.values(this.graficosMF).forEach(g => g?.destroy());
      this.graficosMF = {};
      await this.cargarCurvasPertenencia();

      this.ejecutarInferencia();
      this.superficieCargada = false;

      this.actualizarStatus("Coordenadas restablecidas a valores base ASHRAE / Dell.", false);
    } catch (err) {
      console.error("Error restableciendo coordenadas:", err);
    }
  },

  // Carga y renderizado de las 4 funciones de pertenencia con Chart.js
  async cargarCurvasPertenencia() {
    try {
      const res = await fetch("/api/curvas-pertenencia");
      const datos = await res.json();

      const paletaColores = {
        temperatura_rack: [
          { border: "#0284c7", bg: "rgba(2, 132, 199, 0.14)" },
          { border: "#16a34a", bg: "rgba(22, 163, 74, 0.14)" },
          { border: "#eab308", bg: "rgba(234, 179, 8, 0.14)" },
          { border: "#dc2626", bg: "rgba(220, 38, 38, 0.14)" }
        ],
        uso_cpu: [
          { border: "#0284c7", bg: "rgba(2, 132, 199, 0.14)" },
          { border: "#f59e0b", bg: "rgba(245, 158, 11, 0.14)" },
          { border: "#dc2626", bg: "rgba(220, 38, 38, 0.14)" }
        ],
        temperatura_exterior: [
          { border: "#0284c7", bg: "rgba(2, 132, 199, 0.14)" },
          { border: "#f59e0b", bg: "rgba(245, 158, 11, 0.14)" },
          { border: "#dc2626", bg: "rgba(220, 38, 38, 0.14)" }
        ],
        potencia_enfriamiento: [
          { border: "#dc2626", bg: "rgba(220, 38, 38, 0.14)" },
          { border: "#f59e0b", bg: "rgba(245, 158, 11, 0.14)" },
          { border: "#0284c7", bg: "rgba(2, 132, 199, 0.14)" },
          { border: "#10b981", bg: "rgba(16, 185, 129, 0.14)" }
        ]
      };

      const canvasIds = {
        temperatura_rack: "chartTempRack",
        uso_cpu: "chartUsoCpu",
        temperatura_exterior: "chartTempExt",
        potencia_enfriamiento: "chartPotencia"
      };

      for (const [varName, varData] of Object.entries(datos)) {
        const canvas = document.getElementById(canvasIds[varName]);
        if (!canvas) continue;
        canvas.style.cursor = "crosshair";
        const ctx = canvas.getContext("2d");
        const datasets = [];
        let colorIdx = 0;

        for (const [mfName, mfValues] of Object.entries(varData.conjuntos)) {
          const colorObj = (paletaColores[varName] && paletaColores[varName][colorIdx]) 
            ? paletaColores[varName][colorIdx] 
            : { border: "#0284c7", bg: "rgba(2, 132, 199, 0.14)" };

          datasets.push({
            label: mfName,
            data: mfValues.map((y, i) => ({ x: varData.x[i], y })),
            borderColor: colorObj.border,
            backgroundColor: colorObj.bg,
            borderWidth: 2,
            tension: 0,
            fill: true,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHitRadius: 15
          });
          colorIdx++;
        }

        this.graficosMF[varName] = new Chart(ctx, {
          type: "line",
          data: { datasets },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: {
              mode: "index",
              intersect: false
            },
            hover: {
              mode: "index",
              intersect: false
            },
            scales: {
              x: {
                type: "linear",
                title: { display: true, text: varData.etiqueta_x, font: { size: 10 } },
                grid: { color: "#eef2f6" }
              },
              y: {
                min: 0,
                max: 1.05,
                title: { display: true, text: "Grado de Pertenencia (μ)", font: { size: 10 } },
                grid: { color: "#eef2f6" }
              }
            },
            plugins: {
              legend: {
                position: "top",
                labels: { boxWidth: 12, font: { size: 9 } }
              },
              tooltip: {
                enabled: true,
                mode: "index",
                intersect: false,
                backgroundColor: "rgba(16, 42, 67, 0.95)",
                titleFont: { size: 12, weight: "bold" },
                bodyFont: { size: 11 },
                padding: 8,
                cornerRadius: 4,
                borderColor: "#334e68",
                borderWidth: 1,
                callbacks: {
                  title: function(items) {
                    if (!items || !items.length) return "";
                    const xVal = items[0].parsed.x;
                    return `${varData.etiqueta_x}: ${xVal.toFixed(1)}`;
                  },
                  label: function(item) {
                    const mfName = item.dataset.label || "";
                    const muVal = item.parsed.y;
                    if (muVal > 0.001) {
                      return `  ● ${mfName}: μ = ${muVal.toFixed(3)}`;
                    }
                    return `    ${mfName}: μ = 0.000`;
                  }
                }
              }
            }
          }
        });
      }
      this.renderizarMiniPlotsFIS(datos);

      // Si todavía no hay reglas agregadas, mostrar las funciones de pertenencia en la tarjeta de salida
      if (!this.reglas || this.reglas.length === 0) {
        this.renderizarCurvasPertenenciaSalida();
      }
    } catch (err) {
      console.error("Error cargando curvas de pertenencia:", err);
    }
  },

  // Renderizar mini curvas dentro de cada bloque del diagrama FIS (Réplica MATLAB)
  renderizarMiniPlotsFIS(datos) {
    if (!datos) return;
    this.ultimosDatosCurvas = datos;

    const paletaColores = {
      temperatura_rack: ["#0284c7", "#16a34a", "#eab308", "#dc2626"],
      uso_cpu: ["#0284c7", "#f59e0b", "#dc2626"],
      temperatura_exterior: ["#0284c7", "#f59e0b", "#dc2626"],
      potencia_enfriamiento: ["#dc2626", "#f59e0b", "#0284c7", "#10b981"]
    };

    const vars = ["temperatura_rack", "uso_cpu", "temperatura_exterior", "potencia_enfriamiento"];
    vars.forEach(varKey => {
      const varData = datos[varKey];
      if (!varData || !varData.x || !varData.conjuntos) return;
      const canvas = document.getElementById(`miniPlot-${varKey}`);
      if (!canvas) return;

      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      const cssW = (rect.width && rect.width > 20) ? rect.width : 160;
      const cssH = (rect.height && rect.height > 20) ? rect.height : 68;

      canvas.width = Math.round(cssW * dpr);
      canvas.height = Math.round(cssH * dpr);

      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Fondo blanco limpio
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const padX = 8 * dpr;
      const padBottom = 6 * dpr;
      const padTop = 6 * dpr;
      const plotW = canvas.width - (2 * padX);
      const plotH = canvas.height - padBottom - padTop;
      const baselineY = canvas.height - padBottom;

      // Eje de base X en gris
      ctx.strokeStyle = "#cbd5e1";
      ctx.lineWidth = 1 * dpr;
      ctx.beginPath();
      ctx.moveTo(padX, baselineY);
      ctx.lineTo(canvas.width - padX, baselineY);
      ctx.stroke();

      const xMin = varData.x[0];
      const xMax = varData.x[varData.x.length - 1];
      const xSpan = (xMax - xMin) || 1;

      let cIdx = 0;
      for (const [mfName, mfValues] of Object.entries(varData.conjuntos)) {
        const color = (paletaColores[varKey] && paletaColores[varKey][cIdx])
          ? paletaColores[varKey][cIdx]
          : "#0076a8";

        ctx.strokeStyle = color;
        ctx.lineWidth = 1.8 * dpr;
        ctx.lineJoin = "round";
        ctx.beginPath();

        for (let i = 0; i < varData.x.length; i++) {
          const xVal = varData.x[i];
          const yVal = Math.max(0, Math.min(1, mfValues[i]));

          const px = padX + ((xVal - xMin) / xSpan) * plotW;
          const py = baselineY - (yVal * plotH);

          if (i === 0) {
            ctx.moveTo(px, py);
          } else {
            ctx.lineTo(px, py);
          }
        }
        ctx.stroke();
        cIdx++;
      }
    });
  },

  // Trazar flechas de conexión curvas entre bloques en el lienzo SVG del FIS
  dibujarConectoresFIS() {
    const svg = document.getElementById("fisConnectorsSvg");
    const stage = document.getElementById("fisStageCanvas");
    const centerBox = document.querySelector(".fis-center-box");
    if (!svg || !stage || !centerBox) return;

    const stageRect = stage.getBoundingClientRect();
    const centerRect = centerBox.getBoundingClientRect();
    if (stageRect.width === 0 || centerRect.width === 0) return;

    // Preservar marcadores <defs>
    const defs = svg.querySelector("defs");
    svg.innerHTML = "";
    if (defs) {
      svg.appendChild(defs);
    }

    // 1. Flechas desde cada tarjeta de entrada hacia el bloque central Mamdani
    const inputs = ["temperatura_rack", "uso_cpu", "temperatura_exterior"];
    inputs.forEach(id => {
      const card = document.getElementById(`fisCard-${id}`);
      if (!card) return;
      const cardRect = card.getBoundingClientRect();

      const x1 = cardRect.right - stageRect.left;
      const y1 = cardRect.top + cardRect.height / 2 - stageRect.top;

      const x2 = centerRect.left - stageRect.left;
      const y2 = centerRect.top + centerRect.height / 2 - stageRect.top;

      const dx = (x2 - x1) * 0.45;

      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`);
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", "#0284c7");
      path.setAttribute("stroke-width", "2");
      path.setAttribute("marker-end", "url(#arrowhead-in)");
      svg.appendChild(path);
    });

    // 2. Flecha desde el bloque central Mamdani hacia la salida
    const outCard = document.getElementById("fisCard-potencia_enfriamiento");
    if (outCard) {
      const cardRect = outCard.getBoundingClientRect();
      const x1 = centerRect.right - stageRect.left;
      const y1 = centerRect.top + centerRect.height / 2 - stageRect.top;

      const x2 = cardRect.left - stageRect.left;
      const y2 = cardRect.top + cardRect.height / 2 - stageRect.top;

      const dx = (x2 - x1) * 0.45;

      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`);
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", "#ea580c");
      path.setAttribute("stroke-width", "2");
      path.setAttribute("marker-end", "url(#arrowhead-out)");
      svg.appendChild(path);
    }
  },

  // Carga y renderizado de la Superficie 3D con Plotly
  async cargarSuperficie3D(tempParam) {
    let tempExt;
    if (tempParam !== undefined && tempParam !== null && !isNaN(parseFloat(tempParam))) {
      tempExt = parseFloat(tempParam);
    } else {
      const inputEl = document.getElementById("inputSurfaceExt");
      const sliderEl = document.getElementById("sliderSurfaceExt");
      tempExt = inputEl ? parseFloat(inputEl.value) : (sliderEl ? parseFloat(sliderEl.value) : 20.0);
    }
    if (isNaN(tempExt)) tempExt = 20.0;
    tempExt = Math.max(0, Math.min(45, Math.round(tempExt * 10) / 10));

    const inputEl = document.getElementById("inputSurfaceExt");
    if (inputEl && parseFloat(inputEl.value) !== tempExt) {
      inputEl.value = tempExt.toFixed(1);
    }

    const btnRecalc = document.getElementById("btnActualizarSuperficie");
    if (btnRecalc) {
      btnRecalc.disabled = true;
      btnRecalc.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Recalculando...`;
    }

    this.actualizarStatus(`Calculando superficie de control 3D para Temp Ext = ${tempExt.toFixed(1)} °C...`, true);

    try {
      const res = await fetch(`/api/superficie-3d?temp_ext=${tempExt}`);
      const data = await res.json();

      const trace = {
        z: data.z,
        x: data.x,
        y: data.y,
        type: "surface",
        colorscale: "Viridis",
        contours: {
          z: { show: true, usecolormap: true, highlightcolor: "#42f4eb", project: { z: false } }
        }
      };

      const layout = {
        title: {
          text: `Superficie de Control Difuso (Temp Exterior = ${tempExt.toFixed(1)} °C)`,
          font: { size: 13, family: "Segoe UI, sans-serif" }
        },
        scene: {
          xaxis: { 
            title: { text: "Temp. Rack (°C)", font: { size: 11, color: "#102a43" } } 
          },
          yaxis: { 
            title: { text: "Uso CPU (%)", font: { size: 11, color: "#102a43" } } 
          },
          zaxis: { 
            title: { text: "Potencia HVAC (%)", font: { size: 11, color: "#102a43" } } 
          },
          camera: { eye: { x: 1.8, y: -1.5, z: 1.15 } }
        },
        margin: { l: 30, r: 30, b: 30, t: 40 },
        paper_bgcolor: "#ffffff"
      };

      Plotly.newPlot("plotSuperficie3D", [trace], layout, { responsive: true });
      this.superficieCargada = true;
      this.actualizarStatus("Superficie 3D calculada exitosamente.", false);
    } catch (err) {
      console.error("Error al cargar superficie 3D:", err);
      this.actualizarStatus("Error calculando superficie 3D.", false);
    } finally {
      if (btnRecalc) {
        btnRecalc.disabled = false;
        btnRecalc.innerHTML = `<i class="fa-solid fa-rotate"></i> Recalcular Superficie`;
      }
    }
  },





  // Actualizar estado en la barra inferior
  actualizarStatus(mensaje, cargando = false) {
    const el = document.getElementById("statusbarText");
    const dot = document.getElementById("statusDot");
    el.textContent = mensaje;
    dot.style.backgroundColor = cargando ? "#d97706" : "#198754";
  }
};

// Iniciar aplicación al cargar el DOM
window.addEventListener("DOMContentLoaded", () => {
  app.init();
});
