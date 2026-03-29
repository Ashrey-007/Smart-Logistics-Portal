document.addEventListener("DOMContentLoaded", () => {
    const labelsNode = document.getElementById("chart-labels");
    const valuesNode = document.getElementById("chart-values");
    const chartNode = document.getElementById("shipmentChart");
    if (!labelsNode || !valuesNode || !chartNode || !window.Chart) return;

    // Parse labels and values
    const labels = JSON.parse(labelsNode.textContent);
    const dataValues = JSON.parse(valuesNode.textContent);
    
    // Set up beautiful modern slate/indigo compatible solid colors
    const colors = ["#4f46e5", "#06b6d4", "#10b981", "#f59e0b", "#8b5cf6", "#f43f5e"];
    
    new Chart(chartNode, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: dataValues,
                backgroundColor: colors.slice(0, labels.length),
                hoverOffset: 6,
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    labels: {
                        boxWidth: 12,
                        padding: 15,
                        usePointStyle: true,
                        font: {
                            family: "'Outfit', 'Inter', sans-serif",
                            size: 12,
                            weight: '600'
                        },
                        color: "#64748b"
                    }
                },
                tooltip: {
                    backgroundColor: "#0f172a",
                    titleFont: { family: "'Outfit', 'Inter', sans-serif", size: 13, weight: '700' },
                    bodyFont: { family: "'Outfit', 'Inter', sans-serif", size: 12 },
                    padding: 10,
                    cornerRadius: 8,
                    displayColors: true
                }
            },
            cutout: "70%"
        }
    });
});
