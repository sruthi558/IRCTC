import { useEffect, useRef, useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import styles from "./case_overview.module.scss";
import { DateRangePicker, SelectPicker } from "rsuite";

// const COLORS = ['#845ef7', '#5c7cfa', '#339af0'];
// const COLORS = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12'];
// const COLORS = ['#5e2a72', '#c4a35a', '#6a0572'];
// const COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c'];
const COLORS = ["#ff6b6b", "#4caf50", "#ffc107"];
// const COLORS = ['#ff6361', '#bc5090','#ffa600'];

const RADIAN = Math.PI / 180;

const collectionDateData = [
  { label: 'Last Week', value: 'last_week' },
  { label: 'Last 15 Days', value: 'last_15_days' },
  { label: 'Last Month', value: 'last_month' },
  { label: 'Last Three Months', value: 'last_three_month' },
];


// const getLast30DaysRange = () => {
//   const endDate = new Date();
//   const startDate = new Date();
//   startDate.setDate(endDate.getDate() - 30); // 30 days ago

//   return [startDate, endDate];
// };

const Piechart = () => {
  const [activeIndex, setActiveIndex] = useState(null);
  // const [dateRange, setDateRange] = useState(getLast30DaysRange());
  const [data, setData] = useState([]);
  const [selectFilterDate, setSelectFilterDate] = useState('last_week')
  const isInitialRender = useRef(true);

  const handleOptionSelect = (newValue) => {
    setSelectFilterDate(newValue);
    if (!isInitialRender.current) {
      // Perform API call only if it's not the initial render
      fetchData(newValue);
    }
  };

  const formatData = (data) => {
    if (Array.isArray(data) && data.length > 0) {
      const formattedData = data.map((item) => {
        const severity = Object.keys(item)[0];
        const { IP, PNR, USER, TOTAL, PERCENTAGE } = item[severity];
        // console.log(`Severity: ${severity}, IP: ${IP}, PNR: ${PNR}, USER: ${USER}, TOTAL: ${TOTAL}, PERCENTAGE: ${PERCENTAGE}`);
        return {
          name: severity,
          value: TOTAL,
          IP,
          PNR,
          USER,
          percentage: PERCENTAGE,
        };
      });

      // console.log("Formatted Data:", formattedData);
      return formattedData;
    }

    return [];
  };

  // const formatData = (data) => {
  //   console.log('data', data)
  //   if (Array.isArray(data) && data.length > 0) {
  //     const formattedData = data.map((item) => {
  //       console.log('formattedData', formattedData)
  //       const severity = Object.keys(item)[0];
  //       const { IP, PNR, USER, TOTAL, PERCENTAGE } = item[severity];
  //       console.log(`Severity: ${severity}, IP: ${IP}, PNR: ${PNR}, USER: ${USER}, TOTAL: ${TOTAL}, PERCENTAGE: ${PERCENTAGE}`);
  //       return { name: severity, value: TOTAL, IP, PNR, USER, percentage: PERCENTAGE };
  //     });

  //     console.log('Formatted Data:', formattedData);
  //     return formattedData.filter((item) => item.percentage >= 1); // Adjust the threshold as needed
  //   }

  //   return [];
  // };

  const fetchData = async (selectFilterDate) => {
    try {
      const response = await fetch("/api/overview-severity", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          filter_date:selectFilterDate,
        }),
      });

      const result = await response.json();
      const formattedData = formatData(result.data_list);
      setData(formattedData);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  const RADIAN = Math.PI / 180;
  const renderCustomizedLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
    payload,
  }) => {
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    // console.log(
    //   `x: ${x}, y: ${y}, midAngle: ${midAngle}, payload:`,
    //   payload.percentage
    // );
    // console.log("cs", cx);

    return (
      <text
        x={x}
        y={y}
        fill="white"
        labelLine={false}
        outerRadius={80}
        textAnchor="middle"
        dominantBaseline="central"
      >
        {`${payload?.percentage.toFixed(2)}%`}
      </text>
    );
  };
  const calculateMinAngle = (data) => {
    const minPercentage = Math.min(...data.map((entry) => entry.percentage));
    const minAngle = (minPercentage / 100) * 360;
    // console.log("minAngle", minAngle);
    return minAngle;
  };

  const minAngle = calculateMinAngle(data);

  const onPieEnter = (_, index) => {
    setActiveIndex(index);
  };

  // const handleDateRangeChange = (value) => {
  //   setDateRange(value);
  // };

  // const formatDate = (item) => {
  //   const date = Object.entries(item)[0];
  //   const formattedDate = format(new Date(date[0]), "dd-MM-yyyy"); // Format date as dd-mm-yyyy
  //   return formattedDate;
  // };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const values = payload[0]?.payload;
      const severity = values.name;

      return (
        <div className={styles.customTooltip}>
          <div className={styles.tooltipSection}>
            <div className={styles.tooltipCategory}>
              <p className={styles[`tooltipHeader${severity}`]}>{severity}</p>
              <p>{`IP: ${values.IP}`}</p>
              <p>{`PNR: ${values.PNR}`}</p>
              <p>{`USER: ${values.USER}`}</p>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  const totalCounts = {
    HIGH: data.reduce(
      (total, entry) => (entry.name === "HIGH" ? total + entry.value : total),
      0
    ),
    MEDIUM: data.reduce(
      (total, entry) => (entry.name === "MEDIUM" ? total + entry.value : total),
      0
    ),
    LOW: data.reduce(
      (total, entry) => (entry.name === "LOW" ? total + entry.value : total),
      0
    ),
  };
  
  useEffect(() => {
    isInitialRender.current = false;
    fetchData(selectFilterDate);
  }, []); 


  return (
    <>
      {/* <div className={styles.inputcontainer}>
        <DateRangePicker
          value={dateRange}
          onChange={handleDateRangeChange}
          className={styles.dateFilterInput}
          cleanable={false}
          format="dd-MM-yyyy"
          placement="leftStart"
        />
      </div> */}
      <div className={styles.datecontainer}>
      <SelectPicker
        value={selectFilterDate}
        data={collectionDateData}
        // label='Select Date'
        onChange={(newValue) => handleOptionSelect(newValue)}
        className={styles.dateFilterStyles}
        searchable={false}
        appearance="default"
        // style={{ backgroundColor: selectFilterDate ? 'white' : 'red' }}
        // menuStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.8)' }}
        hoverStyle={{ backgroundColor: 'black' }}
      />
  </div>
      <div className={styles.parent_piechart_container}>
        <ResponsiveContainer
          width="100%"
          height={300}
          className={styles.child_piechart_1}
        >
          <PieChart width="100%" height="100%">
            <Pie
              data={data}
              cx="50%"
              cy="44%"
              labelLine={false}
              label={renderCustomizedLabel}
              outerRadius={120}
              fill="#8884d8"
              dataKey="value"
              onMouseEnter={onPieEnter}
              minAngle={minAngle}
              maxRadius={120}
              startAngle={0} // Set startAngle to 0 for clockwise direction
              endAngle={360}
              
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[index % COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        <div className={styles.child_piechart_2}>
          <div className={styles.labelContainer}>
            <ul>
              <li className={styles.TotalAddCount}>
                <div
                 className={styles.totaltextstyle}
                  style={{ backgroundColor: "#00A9FF" }}
                ></div>
                Total
              </li>
              {data.map((entry, index) => (
                <li key={index}>
                  <div
                    className={styles.bubble}
                    style={{ backgroundColor: COLORS[index] }}
                  ></div>
                  {entry.name}
                </li>
              ))}
            </ul>
            <ul className={styles.countNumbers}>
              <li className={styles.TotalAddCount}>
                {totalCounts.HIGH + totalCounts.MEDIUM + totalCounts.LOW}
              </li>
              {data.map((entry, index) => (
                <li key={index}>{entry.value}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </>
  );
};

export default Piechart;
