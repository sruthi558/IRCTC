import dynamic from "next/dynamic";
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

const PiApexChart = (props) => {
  const pastelColors = ["#D71115", "#FF8000","#FFE000", "#FEBC0F"]; // Array of pastel colors

  const options = {
    plotOptions: {
      pie: {
        donut: {
          labels: {
            show: true,
            name: {
              show: true,
              fontSize: "22px",
              fontFamily: "Mulish",
              color: "#dfsda",
              offsetY: -10,
            },
            value: {
              show: true,
              fontSize: "22px",
              fontFamily: "Helvetica, Arial, sans-serif",
              color: "#373d3f",
              offsetY: 16,
              formatter: function (val) {
                return val;
              },
            },
            total: {
              show: props.total ? true : false,
              showAlways: false,
              label: 'Total',
              fontSize: "22px",
              fontFamily: "Helvetica, Arial, sans-serif",
              fontWeight: 600,
              color: "#373d3f",
              formatter: function (w) {
                return props.total;
              },
            },
          },
        },
      },
    },
    labels: props.label,
    legend: {
      show: true,
      fontSize: '15px',
      position: "left",
      horizontalAlign: "left",
      fontFamily: "Mulish",
      floating: false,
      width: 150,
      offsetY: 30,
    },
    title: {
      text: props.title,
      align: "left",
      width: 5,
      style: {
        fontSize: "20px",
        fontWeight: "bold",
        fontFamily: "Mulish",
        color: "#263238",
        opacity: 0.2,
      },
      offsetY: 10
    },
    dataLabels: {
      enabled: false,
      formatter: function (val) {
        return val;
      },
    },
    stroke: { width: 0 },
    chart: {
      events: {
        dataPointSelection: (e, ctxt, config) => {
          props.event_func(config.w.config.labels[config.dataPointIndex]);
        },
      },
    },
    colors: pastelColors, // Assign pastel colors to the chart
  };
  const series = props.series; //our data

  return (
    <Chart
      options={options}
      series={series}
      type="donut"
      width={props.width}
      height={props.height}
    />
  );
};

export default PiApexChart;
