gradientChartOptionsConfiguration = {
    maintainAspectRatio: false,
    legend: {
      display: false
    },
    tooltips: {
      bodySpacing: 4,
      mode: "nearest",
      intersect: 0,
      position: "nearest",
      xPadding: 10,
      yPadding: 10,
      caretPadding: 10
    },
    responsive: true,
    scales: {
      yAxes: [{
        display: 0,
        gridLines: 0,
        ticks: {
          display: false
        },
        gridLines: {
          zeroLineColor: "transparent",
          drawTicks: false,
          display: false,
          drawBorder: false
        }
      }],
      xAxes: [{
        display: 0,
        gridLines: 0,
        ticks: {
          display: false
        },
        gridLines: {
          zeroLineColor: "transparent",
          drawTicks: false,
          display: false,
          drawBorder: false
        }
      }]
    },
    layout: {
      padding: {
        left: 0,
        right: 0,
        top: 15,
        bottom: 15
      }
    }
  };