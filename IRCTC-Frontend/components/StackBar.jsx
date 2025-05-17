import dynamic from "next/dynamic";
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

const StackBarChart = (props) => {
  let options = {
    markers: {
      size: 1
    },
    chart: {
      id: "apexchart-example",
      toolbar: {
        show: false  ,
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
      offsetY: 10
    },
    grid: {
      show: true,
    },
    plotOptions: {
      bar: {
        columnWidth: '80%',
        distributed: false, // this line is mandatory
        horizontal: false,
        barHeight: "85%",
      },
    },
    xaxis: {
      categories: props.labels,
    },
  };
  let series = [
    {
      name: props.vps_count_name,
      data: props.vps_count,
    },
    {
      name: props.non_vps_count_name,
      data: props.non_vps_count,
    },
    {
      name: props.ser3_name,
      data: props.ser3_count,
    },
  ];
  return (
    <Chart
      options={options}
      series={series}
      type="area"
      width={props.width}
      height={props.height}
    />
  );
};

export default StackBarChart;
