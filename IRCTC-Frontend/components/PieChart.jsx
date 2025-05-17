// Import Libraries
import { Chart as ChartJs } from 'chart.js/auto';
import { CategoryScale, Tooltip, Title, ArcElement, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJs.register(Tooltip, Title, ArcElement, Legend, CategoryScale);

// PieChart Component
function PieChart({inputData, inputLabels, chartTitle, displayCount, backgroundColor, borderColor, label}) {

  const options = {
    responsive: true,
    plugins: {
      scales: {
        x: {
            grid: {
              offset: true
            }
        }
    },
      legend: {
        position: 'top',
        labels: {
          // This more specific font property overrides the global property
          font: {
              size: 13
          }
      }
      },
      title: {
        display: true,
        text: chartTitle,
      }               
    }
  };

  // 
  const data = {
    labels: inputLabels.slice(0, displayCount),
    datasets: [
      {
        label: label,
        data: inputData.slice(0, displayCount),
        borderColor: borderColor,
        backgroundColor: backgroundColor,
        borderWidth: 2,
        hoverBackgroundColor: 'rgba(255, 0, 99, 0.5)',
        barThickness: 'flex'
      },
    ],
  };

  // Render
  return (
    <Pie data={data} options={options}/>
  );
}

export default PieChart;
