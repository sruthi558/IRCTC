import dynamic from "next/dynamic";
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

const BarApexChart = (props) => {
  let options = {
    markers: {
      size: 1
    },
    chart: {
      id: "barApexChart",
      toolbar: {
        show: false
      }
    },
    title: {
      text: props.title,
      width: 10,
      style: {
        fontSize: "20px",
        fontWeight: "bold",
        fontFamily: "Mulish",
        color: "#263238",
        opacity: 0.2,
      },
      offsetY: 10,
    },
    grid: {
      show: false,
    },
    dataLabels: {
      enabled: props.dataLabels,
    },
    plotOptions: {
      bar: {
        columnWidth: '80%',
        distributed: false, // this line is mandatory
        horizontal: false,
        barHeight: "85%",
        dataLabels: {
          enabled: false,
          position: 'top',
          maxItems: 100,
          hideOverflowingLabels: false,
          offsetY: 30,
          total: {
            enabled: false,
            formatter: undefined,
            offsetX: 0,
            offsetY: 0,
            style: {
              color: '#373d3f',
              fontSize: '12px',
              fontFamily: undefined,
              fontWeight: 600
            }
          }
      },
      },
    },
    xaxis: {
      categories: props.labels,
    }
  };

  let series=[{
    name: 'count',
    data: props.series  
  }]
  return (
    <Chart
      options={options}
      series={series}
      type="bar"
      width={props.width}
      height={props.height}
    />
  );
};

export default BarApexChart;
