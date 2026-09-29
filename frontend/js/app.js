/**
 * MATLAB Fuzzy Logic Designer - Lógica del Frontend
 * Integración con Backend: Control Difuso (Mamdani), Algoritmo Genético
 */

const app = {
  reglas: [],
  reglaSeleccionada: null,
  graficosMF: {},
  graficoGA: null,
  graficoAgregacion: null,
  superficieCargada: false,
  debounceTimer: null,

  // Inicialización
  async init() {
    this.enlazarEventos();
    await this.cargarEstadoInicial();
    await this.cargarCurvasPertenencia();
    this.ejecutarInferencia();
    this.actualizarTemperaturaFijaComparacion(18.0);
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


    // Subir dataset CSV
    const inputCSV = document.getElementById("inputArchivoCSV");
    const btnSubir = document.getElementById("btnSubirDataset");
    if (btnSubir && inputCSV) {
      btnSubir.addEventListener("click", () => {
        if (!btnSubir.disabled) inputCSV.click();
      });
      inputCSV.addEventListener("change", (e) => this.subirDatasetCSV(e));
    }

    // Algoritmo Genético
    const btnGA = document.getElementById("btnEjecutarGA");
    if (btnGA) {
      btnGA.addEventListener("click", () => this.ejecutarAlgoritmoGenetico());
    }

    // Cambio dinámico de Temperatura Fija de Comparación
    const inputTempFija = document.getElementById("gaTempFija");
    if (inputTempFija) {
      inputTempFija.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value) || 18.0;
        this.actualizarTemperaturaFijaComparacion(val);
      });
    }

    // Superficie 3D controles
    const sliderSurf = document.getElementById("sliderSurfaceExt");
    if (sliderSurf) {
      sliderSurf.addEventListener("input", (e) => {
        document.getElementById("valSurfaceExt").textContent = `${parseFloat(e.target.value).toFixed(1)} °C`;
      });
      sliderSurf.addEventListener("change", () => this.cargarSuperficie3D());
    }
    const btnSurf = document.getElementById("btnActualizarSuperficie");
    if (btnSurf) {
      btnSurf.addEventListener("click", () => this.cargarSuperficie3D());
    }

    // Sliders de Inferencia en Tiempo Real
    const sliders = ["sliderRack", "sliderCpu", "sliderExt"];
    sliders.forEach(id => {
      const sliderEl = document.getElementById(id);
      if (sliderEl) {
        sliderEl.addEventListener("input", () => {
          this.actualizarEtiquetasSliders();
          clearTimeout(this.debounceTimer);
          this.debounceTimer = setTimeout(() => this.ejecutarInferencia(), 40);
        });
      }
    });

    // Exportar reglas (opcional)
    const btnExp = document.getElementById("btnExportarReglas");
    if (btnExp) {
      btnExp.addEventListener("click", () => this.exportarReglasCSV());
    }
  },

  // Cambiar pestaña activa
  activarTab(tabId) {
    document.querySelectorAll(".center-tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

    const tabHead = document.querySelector(`.center-tab[data-tab="${tabId}"]`);
    const tabPane = document.getElementById(tabId);

    if (tabHead && tabPane) {
      tabHead.classList.add("active");
      tabPane.classList.add("active");
    }

    // Si se presiona directamente el panel de Función de Pertenencia, mostrar todos los gráficos
    if (tabId === "tabCurvas") {
      this.mostrarTodosLosGraficosPertenencia();
    }

    if (tabId === "tabSuperficie" && !this.superficieCargada) {
      this.cargarSuperficie3D();
    }
  },

  // Mostrar únicamente el gráfico de una variable seleccionada en el árbol
  mostrarGraficoPertenencia(nombreVariable) {
    // Activar pestaña de curvas sin disparar mostrarTodosLosGraficosPertenencia
    document.querySelectorAll(".center-tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
    const tabHead = document.querySelector(`.center-tab[data-tab="tabCurvas"]`);
    const tabPane = document.getElementById("tabCurvas");
    if (tabHead && tabPane) {
      tabHead.classList.add("active");
      tabPane.classList.add("active");
    }

    // Marcar nodo activo en el árbol
    document.querySelectorAll(".tree-node").forEach(n => n.classList.remove("active"));
    const activeNode = document.getElementById(`treeNode-${nombreVariable}`);
    if (activeNode) activeNode.classList.add("active");

    // Activar modo de vista única en la cuadrícula
    const grid = document.getElementById("membershipGrid");
    if (grid) grid.classList.add("single-view");

    const cards = ["temperatura_rack", "uso_cpu", "temperatura_exterior", "potencia_enfriamiento"];
    cards.forEach(varKey => {
      const card = document.getElementById(`card-${varKey}`);
      if (card) {
        card.style.display = (varKey === nombreVariable) ? "flex" : "none";
      }
    });

    // Mostrar barra informativa de filtro
    const toolbar = document.getElementById("toolbarCurvas");
    if (toolbar) toolbar.style.display = "flex";
    const lbl = document.getElementById("lblFiltroCurvaActiva");
    if (lbl) {
      const nombresHumanos = {
        temperatura_rack: "Entrada: Temperatura Rack (°C)",
        uso_cpu: "Entrada: Uso de CPU (%)",
        temperatura_exterior: "Entrada: Temperatura Exterior (°C)",
        potencia_enfriamiento: "Salida: Potencia de Enfriamiento (%)"
      };
      lbl.innerHTML = `<i class="fa-solid fa-chart-line"></i> ${nombresHumanos[nombreVariable] || nombreVariable}`;
    }

    setTimeout(() => {
      if (this.graficosMF[nombreVariable]) {
        this.graficosMF[nombreVariable].resize();
      }
    }, 40);
  },

  // Mostrar todos los gráficos (las 4 funciones de pertenencia en cuadrícula 2x2)
  mostrarTodosLosGraficosPertenencia() {
    const grid = document.getElementById("membershipGrid");
    if (grid) grid.classList.remove("single-view");

    const cards = ["temperatura_rack", "uso_cpu", "temperatura_exterior", "potencia_enfriamiento"];
    cards.forEach(varKey => {
      const card = document.getElementById(`card-${varKey}`);
      if (card) card.style.display = "flex";
    });

    document.querySelectorAll(".tree-node").forEach(n => n.classList.remove("active"));

    const toolbar = document.getElementById("toolbarCurvas");
    if (toolbar) toolbar.style.display = "none";

    setTimeout(() => {
      Object.values(this.graficosMF).forEach(g => g?.resize());
    }, 40);
  },

  // Cargar estado inicial del sistema desde Flask
  async cargarEstadoInicial() {
    try {
      this.actualizarStatus("Verificando datos del sistema...", true);
      const res = await fetch("/api/estado");
      const data = await res.json();

      // No precargar reglas al iniciar la aplicación:
      this.reglas = [];
      this.renderizarTablaReglas(this.reglas);
      const badgeReglas = document.getElementById("badgeReglasCount");
      if (badgeReglas) badgeReglas.textContent = "0";

      // Si el dataset ya está cargado por defecto, bloquear el botón de subir:
      const btnSubir = document.getElementById("btnSubirDataset");
      const lblEstadoDataset = document.getElementById("lblEstadoDatasetSidebar");
      if (data.dataset_existe) {
        if (btnSubir) {
          btnSubir.disabled = true;
          btnSubir.classList.add("disabled");
          btnSubir.title = `Dataset ya cargado en el sistema (${data.total_registros || 1500} registros).`;
          btnSubir.innerHTML = `<i class="fa-solid fa-lock"></i> <span>Subir CSV</span>`;
        }
        if (lblEstadoDataset) {
          lblEstadoDataset.innerHTML = `<i class="fa-solid fa-circle-check" style="color: #10b981;"></i> Dataset Cargado`;
        }
      }

      this.actualizarStatus("Sistema inicializado. 36 reglas activas cargadas en el controlador Mamdani.", false);
    } catch (err) {
      console.error("Error al cargar estado inicial:", err);
      this.actualizarStatus("Error de conexión con el backend.", false);
    }
  },

  // Renderizar la tabla de reglas exactamente como en el aula de clases
  renderizarTablaReglas(reglas) {
    const tbody = document.getElementById("tbodyReglas");
    tbody.innerHTML = "";

    if (!reglas || reglas.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; padding: 30px 20px; color: #64748b;">
            <div style="font-size: 24px; color: #0284c7; margin-bottom: 6px;"><i class="fa-solid fa-database"></i></div>
            <div style="font-size: 13px; font-weight: 600; color: #334e68;">Dataset Cargado</div>
          </td>
        </tr>`;
      return;
    }

    reglas.forEach((r, idx) => {
      const tr = document.createElement("tr");
      tr.id = `reglaRow_${idx}`;
      
      const consecuente = r.etiqueta_consecuente || "N/A";
      const pesoFormatted = (r.peso !== undefined ? r.peso : 1.0).toFixed(2);
      tr.innerHTML = `
        <td style="text-align: center; font-weight: bold; color: #57606a;">${idx + 1}</td>
        <td><code>${r.texto_regla}</code></td>
        <td style="text-align: center;"><span style="background: #eef2f6; color: #005a82; padding: 2px 6px; border-radius: 3px; font-weight: 600; font-family: var(--font-mono);">${consecuente}</span></td>
        <td style="text-align: center;"><span class="badge-weight">${pesoFormatted}</span></td>
        <td style="text-align: center; font-weight: 600; color: #198754; font-size: 11px;">AND</td>
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

  // Actualizar valores numéricos al mover los sliders
  actualizarEtiquetasSliders() {
    const tempRack = parseFloat(document.getElementById("sliderRack").value).toFixed(1);
    const usoCpu = parseFloat(document.getElementById("sliderCpu").value).toFixed(1);
    const tempExt = parseFloat(document.getElementById("sliderExt").value).toFixed(1);

    document.getElementById("valRack").textContent = `${tempRack} °C`;
    document.getElementById("valCpu").textContent = `${usoCpu} %`;
    document.getElementById("valExt").textContent = `${tempExt} °C`;
  },

  // Inferencia en Tiempo Real
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

      const potencia = data.potencia_enfriamiento.toFixed(1);
      document.getElementById("valPotenciaOutput").textContent = `${potencia} %`;

      // Barra de progreso y color según intensidad
      const barFill = document.getElementById("barPotenciaFill");
      barFill.style.width = `${Math.min(100, Math.max(0, potencia))}%`;

      if (potencia > 75) {
        barFill.style.background = "linear-gradient(to right, #f59e0b, #ef4444)";
      } else if (potencia > 45) {
        barFill.style.background = "linear-gradient(to right, #0076a8, #0ea5e9)";
      } else {
        barFill.style.background = "linear-gradient(to right, #10b981, #06b6d4)";
      }

      // Renderizar gráfico de la figura difusa agregada y línea del centroide
      if (data.curva_agregada) {
        this.renderizarGraficoAgregacion(data.curva_agregada, parseFloat(potencia));
      }
    } catch (err) {
      console.error("Error en inferencia:", err);
    }
  },

  // Renderizar gráfico de Agregación Difusa y Centroide en el panel derecho
  renderizarGraficoAgregacion(curvaAgregada, centroideVal) {
    const canvas = document.getElementById("chartAgregacionDefuzz");
    if (!canvas) return;

    const lblCentroide = document.getElementById("lblCentroideGrafico");
    if (lblCentroide) {
      lblCentroide.textContent = `z* = ${centroideVal.toFixed(1)} %`;
    }

    if (!curvaAgregada || !curvaAgregada.x || curvaAgregada.x.length === 0) return;

    const ctx = canvas.getContext("2d");
    const dataPoints = curvaAgregada.x.map((xVal, i) => ({ x: xVal, y: curvaAgregada.y[i] }));

    const lineaCentroide = [
      { x: centroideVal, y: 0 },
      { x: centroideVal, y: 1.05 }
    ];

    if (this.graficoAgregacion) {
      this.graficoAgregacion.data.datasets[0].data = dataPoints;
      this.graficoAgregacion.data.datasets[1].data = lineaCentroide;
      this.graficoAgregacion.update("none");
      return;
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


  // Subir y procesar nuevo archivo CSV de sensores
  async subirDatasetCSV(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("archivo", file);

    this.actualizarStatus(`Cargando dataset '${file.name}' para perfil de simulación...`, true);

    try {
      const res = await fetch("/api/subir-dataset", {
        method: "POST",
        body: formData
      });
      const data = await res.json();

      if (data.error) {
        alert(data.error);
        this.actualizarStatus(data.error, false);
        return;
      }

      this.reglas = data.reglas || [];
      this.renderizarTablaReglas(this.reglas);

      const lblTotalS = document.getElementById("lblTotalReglasSidebar");
      if (lblTotalS) lblTotalS.textContent = this.reglas.length;
      const lblTreeS = document.getElementById("lblTreeReglasCount");
      if (lblTreeS) lblTreeS.textContent = this.reglas.length;
      document.getElementById("badgeReglasCount").textContent = this.reglas.length;

      this.actualizarStatus(data.mensaje, false);
      const lblDataset = document.getElementById("lblEstadoDatasetSidebar");
      if (lblDataset) {
        lblDataset.innerHTML = `<i class="fa-solid fa-circle-check" style="color: #10b981;"></i> Dataset Cargado`;
      }
      const btnSubir = document.getElementById("btnSubirDataset");
      if (btnSubir) {
        btnSubir.disabled = true;
        btnSubir.classList.add("disabled");
        btnSubir.title = `Dataset ya cargado (${data.total_registros || 1500} registros)`;
        btnSubir.innerHTML = `<i class="fa-solid fa-lock"></i> <span>Subir CSV</span>`;
      }
      this.ejecutarInferencia();
    } catch (err) {
      console.error("Error al subir dataset:", err);
      this.actualizarStatus("Error al cargar el dataset CSV.", false);
    } finally {
      event.target.value = "";
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
    } catch (err) {
      console.error("Error cargando curvas de pertenencia:", err);
    }
  },

  // Carga y renderizado de la Superficie 3D con Plotly
  async cargarSuperficie3D() {
    const tempExt = parseFloat(document.getElementById("sliderSurfaceExt").value) || 20.0;
    this.actualizarStatus(`Calculando superficie de control 3D para Temp Ext = ${tempExt} °C...`, true);

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
    }
  },

  // Ejecución del Algoritmo Genético
  async ejecutarAlgoritmoGenetico() {
    const poblacion = parseInt(document.getElementById("gaPoblacion").value) || 25;
    const generaciones = parseInt(document.getElementById("gaGeneraciones").value) || 25;
    const tasaMutacionPct = parseFloat(document.getElementById("gaTasaMutacion")?.value) || 20.0;
    const tasaMutacion = Math.max(0.01, Math.min(0.5, tasaMutacionPct / 100.0));
    const tempFija = parseFloat(document.getElementById("gaTempFija")?.value) || 18.0;

    const btn = document.getElementById("btnEjecutarGA");
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Optimizando...`;
    this.actualizarStatus(`Ejecutando GA: Población ${poblacion}, Gen ${generaciones}, Mutación ${(tasaMutacion * 100).toFixed(0)}%...`, true);

    try {
      const res = await fetch("/api/optimizar-genetico", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          poblacion,
          generaciones,
          tasa_mutacion: tasaMutacion,
          temperatura_fija: tempFija
        })
      });
      const data = await res.json();
      this.ultimoResultadoGA = data;

      // Renderizar KPIs (kWh arriba y porcentaje abajo)
      const kwhAhorro = data.ahorro_kwh_diario !== undefined 
        ? data.ahorro_kwh_diario.toFixed(1) 
        : ((data.consumo_kwh_estandar || 0) - (data.consumo_kwh_optimizado || 0)).toFixed(1);
      const elKwh = document.getElementById("gaAhorroKwh");
      if (elKwh) elKwh.textContent = `${kwhAhorro} kWh/día`;
      const elPct = document.getElementById("gaPorcentajeAhorro");
      if (elPct) elPct.textContent = `${data.ahorro_porcentaje.toFixed(1)} % de Ahorro`;
      const elUsd = document.getElementById("gaAhorroDolares");
      if (elUsd) elUsd.textContent = `$ ${data.ahorro_estimado_usd_mes.toFixed(0)} USD/mes`;

      // Reflejar la temperatura fija en la columna de la tabla
      this.actualizarTemperaturaFijaComparacion(tempFija);

      // Actualizar tabla de temperaturas objetivo óptimas
      const listaTemperaturas = data.temperaturas_objetivo_optimas || data.setpoints_optimos || [];
      listaTemperaturas.forEach((sp, idx) => {
        const el = document.getElementById(`sp${idx}`);
        if (el) el.textContent = `${sp.toFixed(2)} °C`;
      });

      // Actualizar métricas de consumo y gasto del Algoritmo Genético (AG)
      const elConsumoOptDia = document.getElementById("lblConsumoOptDiaKwh");
      if (elConsumoOptDia && data.consumo_kwh_optimizado !== undefined) {
        elConsumoOptDia.textContent = `${data.consumo_kwh_optimizado.toFixed(1)} kWh`;
      }
      const elGastoDiarioOpt = document.getElementById("lblGastoDiarioOpt");
      if (elGastoDiarioOpt && data.costo_diario_optimizado !== undefined) {
        elGastoDiarioOpt.textContent = `$ ${data.costo_diario_optimizado.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD/día`;
      }
      const elConsumoOptMes = document.getElementById("lblConsumoOptMesKwh");
      if (elConsumoOptMes && data.consumo_kwh_optimizado !== undefined) {
        const consumoMesOpt = Math.round(data.consumo_kwh_optimizado * 30.0).toLocaleString("en-US");
        elConsumoOptMes.textContent = `${consumoMesOpt} kWh`;
      }
      const elGastoMensualOpt = document.getElementById("lblGastoMensualOpt");
      if (elGastoMensualOpt && data.costo_diario_optimizado !== undefined) {
        const gastoMesOpt = (data.costo_diario_optimizado * 30.0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        elGastoMensualOpt.textContent = `$ ${gastoMesOpt} USD/mes`;
      }

      // Graficar curva de convergencia exactamente como en el gráfico del docente
      this.renderizarGraficoGA(data.historial_mejor, data.historial_promedio);

      // Sincronizar superficie 3D con la nueva tabla de reglas evolucionada
      this.superficieCargada = false;
      const tabSuperficie = document.getElementById("tabSuperficie");
      if (tabSuperficie && tabSuperficie.classList.contains("active")) {
        this.cargarSuperficie3D();
      }

      this.actualizarStatus("Optimización genética completada con éxito.", false);
    } catch (err) {
      console.error("Error en optimización genética:", err);
      this.actualizarStatus("Error al ejecutar algoritmo genético.", false);
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-play"></i> Iniciar Optimización Genética`;
    }
  },

  // Renderizar gráfico de convergencia con Chart.js
  renderizarGraficoGA(mejorFitness, promedioFitness) {
    const ctx = document.getElementById("chartConvergenciaGA").getContext("2d");
    const labels = mejorFitness.map((_, i) => `G${i + 1}`);

    if (this.graficoGA) {
      this.graficoGA.destroy();
    }

    this.graficoGA = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Menor Costo USD al Día",
            data: mejorFitness,
            borderColor: "#0000ff",
            backgroundColor: "#0000ff",
            borderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            tension: 0
          },
          {
            label: "Costo Promedio Población USD al Día",
            data: promedioFitness,
            borderColor: "#008000",
            borderDash: [5, 5],
            borderWidth: 1.8,
            pointRadius: 0,
            tension: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            title: { display: true, text: "Generación Evolutiva", font: { size: 10 } },
            grid: { color: "#eef2f6" }
          },
          y: {
            title: { display: true, text: "Valor Fitness", font: { size: 10 } },
            grid: { color: "#eef2f6" }
          }
        },
        plugins: {
          legend: {
            position: "bottom",
            labels: { boxWidth: 15, font: { size: 10 } }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const label = context.dataset.label || "";
                const val = context.parsed.y;
                return `${label}: ${val} (Costo: $ ${Math.abs(val).toFixed(2)} USD/día)`;
              }
            }
          }
        }
      }
    });
  },

  // Cálculo termodinámico y económico evaluado exclusivamente en el backend Python
  async calcularConsumoYGastoFijo(tempFija) {
    try {
      const res = await fetch(`/api/evaluar-temp-fija?temp=${tempFija}`);
      if (res.ok) {
        return await res.json();
      }
    } catch (err) {
      console.error("Error al consultar evaluación de temperatura fija en el backend:", err);
    }
    return null;
  },

  // Actualizar visualmente la columna fija, etiquetas de consumo y gasto mensual
  async actualizarTemperaturaFijaComparacion(tempFija) {
    const val = parseFloat(tempFija) || 18.0;
    const tempFormateada = `${val.toFixed(1)} °C`;
    document.querySelectorAll(".col-temp-fija").forEach(td => {
      td.textContent = tempFormateada;
    });

    const metricas = await this.calcularConsumoYGastoFijo(val);
    if (metricas) {
      const lblDia = document.getElementById("lblConsumoFijoDiaKwh");
      if (lblDia) lblDia.textContent = `${metricas.consumo_diario_kwh.toFixed(1)} kWh`;

      const lblGastoDia = document.getElementById("lblGastoDiarioFijo");
      if (lblGastoDia) {
        lblGastoDia.textContent = `$ ${metricas.costo_diario_usd.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD/día`;
      }

      const lblMes = document.getElementById("lblConsumoFijoMesKwh");
      if (lblMes) {
        const consumoMesFormateado = Math.round(metricas.consumo_mensual_kwh).toLocaleString("en-US");
        lblMes.textContent = `${consumoMesFormateado} kWh`;
      }

      const lblGasto = document.getElementById("lblGastoMensualFijo");
      if (lblGasto) {
        lblGasto.textContent = `$ ${metricas.costo_mensual_usd.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD/mes`;
      }
    }

    // Si ya se ejecutó el GA previamente, recalcular el ahorro en tiempo real
    if (this.ultimoResultadoGA && metricas) {
      const consumoOpt = this.ultimoResultadoGA.consumo_kwh_optimizado || 0;
      const costoOptDiario = this.ultimoResultadoGA.costo_diario_optimizado || 0;
      const kwhAhorro = (metricas.consumo_diario_kwh - consumoOpt).toFixed(1);
      const ahorroDiarioUsd = metricas.costo_diario_usd - costoOptDiario;
      const pctAhorro = metricas.costo_diario_usd > 0 
        ? ((ahorroDiarioUsd / metricas.costo_diario_usd) * 100).toFixed(1) 
        : "0.0";
      const ahorroMensualUsd = Math.round(ahorroDiarioUsd * 30);

      const elKwh = document.getElementById("gaAhorroKwh");
      if (elKwh) elKwh.textContent = `${kwhAhorro} kWh/día`;
      const elPct = document.getElementById("gaPorcentajeAhorro");
      if (elPct) elPct.textContent = `${pctAhorro} % de Ahorro`;
      const elUsd = document.getElementById("gaAhorroDolares");
      if (elUsd) elUsd.textContent = `$ ${ahorroMensualUsd.toLocaleString()} USD/mes`;

      const elConsumoOptDia = document.getElementById("lblConsumoOptDiaKwh");
      if (elConsumoOptDia && consumoOpt) elConsumoOptDia.textContent = `${consumoOpt.toFixed(1)} kWh`;
      const elGastoDiarioOpt = document.getElementById("lblGastoDiarioOpt");
      if (elGastoDiarioOpt && costoOptDiario) {
        elGastoDiarioOpt.textContent = `$ ${costoOptDiario.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD/día`;
      }
      const elConsumoOptMes = document.getElementById("lblConsumoOptMesKwh");
      if (elConsumoOptMes && consumoOpt) {
        elConsumoOptMes.textContent = `${Math.round(consumoOpt * 30.0).toLocaleString("en-US")} kWh`;
      }
      const elGastoMensualOpt = document.getElementById("lblGastoMensualOpt");
      if (elGastoMensualOpt && costoOptDiario) {
        elGastoMensualOpt.textContent = `$ ${(costoOptDiario * 30.0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD/mes`;
      }
    }
  },

  // Exportar reglas minadas a CSV
  exportarReglasCSV() {
    if (!this.reglas || this.reglas.length === 0) {
      alert("No hay reglas disponibles para exportar.");
      return;
    }

    let csvContent = "data:text/csv;charset=utf-8,ID,Regla,Confianza,Soporte,Nombre\n";
    this.reglas.forEach((r, i) => {
      csvContent += `${i + 1},"${r.texto_regla}",${r.confianza},${r.soporte},${r.nombre}\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "reglas_control_difuso.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
