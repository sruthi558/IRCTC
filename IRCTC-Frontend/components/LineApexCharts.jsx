import dynamic from "next/dynamic";
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

const LineApexChart = (props) => {
  let options = {
    chart: {
      height: 350,
      width: 450,
     
      type: "line",
      zoom: {
        enabled: false,
      }, 

      events: {
        dataPointSelection: (e, ctxt, config) => {
          const month = config.w.config.xaxis.categories[config.dataPointIndex];
          const pageValue = config.w.config.series[0].data[config.dataPointIndex];
          props.event_func(month, pageValue);
        },
      },
    },
    dataLabels: {
      enabled: false,
    },
    // chart: {
    //   toolbar: {
    //     show: false,
    //     tools: {
    //       download: false,
    //     },
    //   },
    // },
    stroke: {
      curve: "smooth",
    },
    title: {
      text: props.title,
      align: "left",
      style: {
        fontSize: "16px",
        fontWeight: "bold",
        fontFamily: "Mulish",
        color: "#263238",
        opacity: 0.2,
      },
      offsetY: 10,
    },
    grid: {
      row: {
        colors: ["#f3f3f3", "transparent"], // takes an array which will be repeated on columns
        opacity: 0.5,
      },
    },
    xaxis: {
      categories: props.label,
      labels: {
        style: {
          fontSize: "10px", 
                
        },
      },
    },
  };
  let series = [
    {
      name: "count",
      data: props.data,
    },
  ];
  return (
    <Chart
      options={options}
      series={series}
      type="bar"
      height={props.height}
      width={props.width}
    />
  );
};

export default LineApexChart;
