// Dashboard JavaScript - Separado del template para evitar errores de sintaxis

// Función para formatear números como pesos chilenos
function formatCLP(amount) {
    if (amount === null || amount === undefined || isNaN(amount)) return '0';
    return Number(amount).toLocaleString('es-CL').replace(/\./g, '.');
}

document.addEventListener('DOMContentLoaded', function() {
    // Esperar a que los datos estén disponibles
    initializeCharts();
    
    // Agregar evento al filtro de mes
    const mesFilter = document.getElementById('mesFilter');
    if (mesFilter) {
        mesFilter.addEventListener('change', function() {
            filterChartsByMonth(this.value);
        });
    }
});

function filterChartsByMonth(mes) {
    // Filtrar datos por mes y actualizar gráficos
    console.log('Filtering charts by month:', mes);
    
    // Llamar a la API del backend para obtener datos filtrados
    fetch(`/api/chart-data?mes=${mes}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateChartsWithFilteredData(data.data);
            } else {
                console.error('Error filtering charts:', data.error);
            }
        })
        .catch(error => {
            console.error('Error calling chart API:', error);
        });
}

function updateChartsWithFilteredData(data) {
    // Actualizar gráficos con datos filtrados
    if (!window.gananciasChart || !window.gastosChart || !window.ingresosVsGastosChart) {
        console.log('Charts not initialized yet');
        return;
    }
    
    // Actualizar gráfico de ganancias manteniendo opciones premium y tooltips
    window.gananciasChart.data = data.ganancias_chart;
    // Mantener los colores de cada rubro definidos en el template
    // No sobrescribir con color azul uniforme
    // Mantener escala logarítmica para que las barras pequeñas sean visibles
    window.gananciasChart.options.scales.y.type = 'logarithmic';
    window.gananciasChart.update('active');
    
    // Actualizar gráfico de gastos manteniendo opciones premium y tooltips
    window.gastosChart.data = data.gastos_chart;
    // Configurar dataset correctamente para el gráfico de gastos
    window.gastosChart.data.datasets[0].borderWidth = 0;
    window.gastosChart.data.datasets[0].hoverOffset = 0;
    window.gastosChart.data.datasets[0].offset = 0;
    window.gastosChart.data.datasets[0].spacing = 0;
    window.gastosChart.data.datasets[0].radius = '90%';
    window.gastosChart.update('active');
    
    // Actualizar gráfico de ingresos vs gastos manteniendo opciones premium y tooltips
    window.ingresosVsGastosChart.data = data.ingresos_vs_gastos_chart;
    // Mantener escala logarítmica para que las barras pequeñas sean visibles
    window.ingresosVsGastosChart.options.scales.y.type = 'logarithmic';
    window.ingresosVsGastosChart.update('active');
    
    // Actualizar números del gráfico de gastos en el template
    updateGastosChartNumbers(data.gastos_chart);
    
    console.log('Charts updated with filtered data and premium styling');
}

function updateGastosChartNumbers(gastosData) {
    // Actualizar los números en el template del gráfico de gastos
    const gastosList = document.querySelector('.gastos-chart-list');
    if (!gastosList) return;
    
    // Validar que los datos existan
    if (!gastosData || !gastosData.labels || !gastosData.datasets || !gastosData.datasets[0]) {
        console.error('Datos de gastos inválidos:', gastosData);
        return;
    }
    
    let html = '';
    const total = gastosData.datasets[0].data.reduce((sum, value) => sum + value, 0);
    
    gastosData.labels.forEach((label, index) => {
        const value = gastosData.datasets[0].data[index];
        const color = gastosData.datasets[0].backgroundColor[index];
        
        // Validar que value no sea null o undefined
        if (value === null || value === undefined) return;
        
        html += `
            <div class="flex items-center justify-between text-sm p-2 bg-gray-50 rounded-lg">
                <div class="flex items-center space-x-2">
                    <div class="w-3 h-3 rounded-full" style="background-color: ${color}"></div>
                    <span class="text-gray-700 font-medium">${label}</span>
                </div>
                <span class="font-bold text-gray-900">$${formatCLP(value)}</span>
            </div>
        `;
    });
    
    html += `
        <div class="pt-2 mt-2 border-t border-gray-200">
            <div class="flex items-center justify-between text-sm font-bold p-2 bg-gray-100 rounded-lg">
                <span class="text-gray-700">Total</span>
                <span class="text-gray-900">$${formatCLP(total)}</span>
            </div>
        </div>
    `;
    
    gastosList.innerHTML = html;
}

function initializeCharts() {
    // Obtener datos del template (inyectados como variables globales)
    if (typeof window.dashboardData === 'undefined') {
        console.error('Datos del dashboard no encontrados');
        return;
    }
    
    const chartData = window.dashboardData;
    
    // Configuración premium común para todos los gráficos
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 750,
            easing: 'easeInOutQuart'
        },
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    padding: 20,
                    font: {
                        size: 13,
                        family: 'Inter, system-ui, -apple-system, sans-serif',
                        weight: '500'
                    },
                    usePointStyle: true,
                    pointStyle: 'circle'
                }
            },
            tooltip: {
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                titleFont: {
                    size: 13,
                    family: 'Inter, system-ui, -apple-system, sans-serif',
                    weight: '600'
                },
                bodyFont: {
                    size: 12,
                    family: 'Inter, system-ui, -apple-system, sans-serif',
                    weight: '400'
                },
                padding: 12,
                cornerRadius: 8,
                displayColors: true,
                boxPadding: 4,
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        const value = context.parsed.y !== undefined ? context.parsed.y : context.parsed;
                        label += '$' + formatCLP(value);
                        return label;
                    }
                }
            }
        },
        scales: {
            x: {
                grid: {
                    display: false,
                    drawBorder: false
                },
                ticks: {
                    font: {
                        size: 11,
                        family: 'Inter, system-ui, -apple-system, sans-serif',
                        weight: '500'
                    },
                    color: '#64748b'
                }
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)',
                    drawBorder: false
                },
                ticks: {
                    font: {
                        size: 11,
                        family: 'Inter, system-ui, -apple-system, sans-serif',
                        weight: '500'
                    },
                    color: '#64748b',
                    callback: function(value) {
                        return '$' + formatCLP(value);
                    }
                }
            }
        },
        interaction: {
            intersect: false,
            mode: 'index'
        }
    };
    
    // Gráfico de Ganancias por Rubro (Bar Chart Premium)
    const gananciasCtx = document.getElementById('gananciasChart');
    if (gananciasCtx && chartData.ganancias_chart.datasets[0].data && chartData.ganancias_chart.datasets[0].data.length > 0) {
        // Mantener los colores de cada rubro definidos en el template
        // No sobrescribir con color azul uniforme
        
        window.gananciasChart = new Chart(gananciasCtx.getContext('2d'), {
            type: 'bar',
            data: chartData.ganancias_chart,
            options: Object.assign({}, commonOptions, {
                scales: {
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            font: {
                                size: 11,
                                family: 'Inter, system-ui, -apple-system, sans-serif',
                                weight: '500'
                            },
                            color: '#64748b'
                        }
                    },
                    y: {
                        type: 'logarithmic',
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            font: {
                                size: 11,
                                family: 'Inter, system-ui, -apple-system, sans-serif',
                                weight: '500'
                            },
                            color: '#64748b',
                            callback: function(value) {
                                if (value === 1000000) return '$1M';
                                if (value === 100000) return '$100k';
                                if (value === 10000) return '$10k';
                                if (value === 1000) return '$1k';
                                if (value === 100) return '$100';
                                return null;
                            }
                        }
                    }
                },
                plugins: {
                    ...commonOptions.plugins,
                    tooltip: {
                        ...commonOptions.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y;
                                return 'Ganancia: $' + formatCLP(value);
                            }
                        }
                    }
                }
            })
        });
    }
    
    // Gráfico de Distribución de Gastos (Pie Chart Premium)
    const gastosCtx = document.getElementById('gastosChart');
    if (gastosCtx && chartData.gastos_chart.datasets[0].data && chartData.gastos_chart.datasets[0].data.length > 0) {
        // Detectar si es mobile
        const isMobile = window.innerWidth < 768;
        
        // Configurar dataset correctamente
        chartData.gastos_chart.datasets[0].borderWidth = 0;
        chartData.gastos_chart.datasets[0].hoverOffset = 0;
        chartData.gastos_chart.datasets[0].offset = 0;
        chartData.gastos_chart.datasets[0].spacing = 0;
        
        // Ajustar tamaño del gráfico según dispositivo
        const chartRadius = isMobile ? 65 : 100;
        
        window.gastosChart = new Chart(gastosCtx.getContext('2d'), {
            type: 'pie',
            data: chartData.gastos_chart,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                animation: false,
                layout: {
                    padding: isMobile ? 10 : 0
                },
                elements: {
                    arc: {
                        borderWidth: 0,
                        borderRadius: 0,
                        hoverOffset: 0,
                        offset: 0
                    }
                },
                plugins: {
                    legend: {
                        display: false // Ocultar legend predeterminado, usamos nuestra propia lista
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleFont: {
                            size: isMobile ? 11 : 13,
                            family: 'Inter, system-ui, -apple-system, sans-serif',
                            weight: '600'
                        },
                        bodyFont: {
                            size: isMobile ? 10 : 12,
                            family: 'Inter, system-ui, -apple-system, sans-serif',
                            weight: '400'
                        },
                        padding: isMobile ? 8 : 12,
                        cornerRadius: 8,
                        displayColors: true,
                        boxPadding: 4,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = '$' + formatCLP(context.parsed);
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return label + ': ' + value + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            },
            plugins: [{
                beforeDraw: function(chart) {
                    // Ajustar manualmente el tamaño del gráfico
                    const width = chart.width;
                    const height = chart.height;
                    const ctx = chart.ctx;
                    
                    // Calcular radio dinámico basado en el tamaño del contenedor
                    const minDimension = Math.min(width, height);
                    const radius = isMobile ? Math.min(minDimension * 0.35, 65) : Math.min(minDimension * 0.4, 100);
                    
                    // Guardar el radio para usar en el render
                    chart.options.elements.arc.outerRadius = radius;
                }
            }]
        });
        
        // Ajustar tamaño del gráfico en resize
        window.addEventListener('resize', function() {
            if (window.gastosChart) {
                const isMobile = window.innerWidth < 768;
                window.gastosChart.update('none');
            }
        });
    }
    
    // Gráfico de Ingresos vs Gastos (Bar Chart Premium)
    const ingresosVsGastosCtx = document.getElementById('ingresosVsGastosChart');
    if (ingresosVsGastosCtx && chartData.ingresos_vs_gastos_chart.datasets[0].data && chartData.ingresos_vs_gastos_chart.datasets[0].data.length > 0) {
        window.ingresosVsGastosChart = new Chart(ingresosVsGastosCtx.getContext('2d'), {
            type: 'bar',
            data: chartData.ingresos_vs_gastos_chart,
            options: Object.assign({}, commonOptions, {
                scales: {
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            font: {
                                size: 11,
                                family: 'Inter, system-ui, -apple-system, sans-serif',
                                weight: '500'
                            },
                            color: '#64748b'
                        }
                    },
                    y: {
                        type: 'logarithmic',
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            font: {
                                size: 11,
                                family: 'Inter, system-ui, -apple-system, sans-serif',
                                weight: '500'
                            },
                            color: '#64748b',
                            callback: function(value) {
                                if (value === 1000000) return '$1M';
                                if (value === 100000) return '$100k';
                                if (value === 10000) return '$10k';
                                if (value === 1000) return '$1k';
                                if (value === 100) return '$100';
                                return null;
                            }
                        }
                    }
                },
                plugins: {
                    ...commonOptions.plugins,
                    legend: {
                        ...commonOptions.plugins.legend,
                        position: 'top'
                    }
                }
            })
        });
    }
}
