import dynamic from "next/dynamic";
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

const BarApex3 = (props) => {
  let options = {
    noData: {  
      text: "Loading...",  
      align: 'center',  
      verticalAlign: 'middle',  
      offsetX: 0,  
      offsetY: 0,  
      style: {  
        color: "#000000",  
        fontSize: '25px',  
        fontFamily: "Helvetica"  
      }  
    },
    markers: {
      size: 1
    },
    chart: {
      id: "apexchart-example",
      toolbar: {
        show: false
      }
    },
    stroke :{
      curve: 'smooth',
    },
    title: {
      text: props.title,
      width: 10,
      style: {
        fontSize: "12px",
        fontFamily: "Mulish",
        color: "#263238",
        opacity: 0.2,
      },
    },
    grid: {
      show: false,
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
      height={300}
    />
  );
};

export default BarApex3;
