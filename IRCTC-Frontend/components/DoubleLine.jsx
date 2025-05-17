import dynamic from "next/dynamic";
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

const BarApexChart = (props) => {
  let options = {
    chart: {
      id: "apexchart-example",
    },
    title: {
      text: props.title,
    },
    grid: {
      show: false,
    },
    stroke: {
      curve: 'smooth',
    },
    markers: {
      size: 1,
  },
    plotOptions: {
      bar: {
        borderRadius: 10,
        borderRadiusApplication: 'around',
        columnWidth: '80%',
        distributed: false, // this line is mandatory
        horizontal: false,
        barHeight: "85%",
      },
    },
    xaxis: {
      categories: [1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999],
    },
  };
  let series = [
    {
      name: "VPS",
      data: [30, 40, 35, 50, 49, 60, 70, 91, 125],
    },
    {
      name: "NON VPS",
      data: [40, 60, 40, 90, 70, 60, 70, 45, 20],
    },
  ];
  return (
    <Chart
      options={options}
      series={series}
      type="line"
      width={500}
      height={380}
    />
  );
};

export default BarApexChart;
