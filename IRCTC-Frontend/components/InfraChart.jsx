import dynamic from "next/dynamic";
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

const PiChart = (props) => {
  const options = {
    colors:[
      "#0046ce",
      "#008300",
      "#988af2",
      "#00c17f",
      "#ff4440",
      "#00f9ff",
      "#ba003e",
      "#00e8ff",
      "#9c2800",
      "#0093e1",
      "#6e7100",
      "#0072ce",
      "#c1d271",
      "#00316b",
      "#fff4ce",
      "#ffabff",
      "#45784f",
      "#637540"
    ],
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
      toolbar: {
        show: true,
        tools: {
          download: true,
        },
      },
      events: {
        dataPointSelection: (e, ctxt, config) => {
        },
      },
    },
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
