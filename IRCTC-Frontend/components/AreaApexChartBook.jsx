// Import Libraries
import dynamic from 'next/dynamic'
const Chart = dynamic(() => import('react-apexcharts'), { ssr: false })

// AreaApexChart Component
const AreaApexChartBook = (props) => {
  let options = {
    markers: {
      size: 1,
    },
    chart: {
      id: 'areaApexChart',
      toolbar: {
        show: false,
      },
    },
    title: {
      text: props.title,
      width: 10,
      style: {
        fontSize: '20px',
        fontWeight: 'bold',
        fontFamily: 'Mulish',
        color: '#263238',
        opacity: 0.2,
      },
      offsetY: 10,
    },
    grid: {
      show: false,
    },
    plotOptions: {
      bar: {
        columnWidth: '80%',
        distributed: false, // this line is mandatory
        horizontal: false,
        barHeight: '85%',
      },
    },
    xaxis: {
      categories: props.labels,
    },
    colors: ['#FF4136', '#2ECC40', '#0074D9', '#FF851B', '#B10DC9'],
    // Replace the color values with the ones you want to use.
  }

  return (
    <Chart
      options={options}
      series={props.series}
      type="area"
      width={props.width}
      height={props.height}
    />
  )
}

export default AreaApexChartBook
