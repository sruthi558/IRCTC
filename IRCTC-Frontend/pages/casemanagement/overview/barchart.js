import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { DateRangePicker } from "rsuite";
import styles from "./case_overview.module.scss";
import { format } from "date-fns";
import { object } from "sharp/lib/is";

const overviewBarCharts = () => {
  const [activeIndex, setActiveIndex] = useState(null);
  const [dateRange, setDateRange] = useState(getLast30DaysRange());
  const [chartData, setChartData] = useState([]);
  useEffect(() => {
    // Make API call when dateRange changes
    const fetchData = async () => {
      try {
        const response = await fetch("/api/overview-weekly", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            starting_date: dateRange[0],
            ending_date: dateRange[1],
          }),
        });

        if (response.ok) {
          const responseData = await response.json();
          setChartData(responseData.data_list);
        } else {
          console.error("Error fetching data");
        }
      } catch (error) {
        console.error("Error:", error);
      }
    };

    fetchData();
  }, [dateRange]);

  function getLast30DaysRange() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - 30); // 30 days ago
    return [startDate, endDate];
  }

  const formatChartData = (data, type) => {
    return data?.map((item) => {
      const [date, values] = Object.entries(item)[0];
      const formattedDate = format(new Date(date), "dd-MM-yyyy"); // Format date as dd-mm-yyyy
      return { date: formattedDate, total: values[type].TOTAL };
    });
  };

  const formatDate = (item) => {
    // return data.map((item) => {
    const date = Object.entries(item)[0];
    // console.log("date", date);
    const formattedDate = format(new Date(date[0]), "dd-MM-yyyy"); // Format date as dd-mm-yyyy
    // return { date: formattedDate, total: values[type].TOTAL };
    return formattedDate;
    // }
    // );
  };

  const sortDataByDate = (data) => {
    return data?.sort((a, b) => new Date(a.date) - new Date(b.date));
  };

  const dataForHigh = sortDataByDate(formatChartData(chartData, "HIGH"));
  const dataForMedium = sortDataByDate(formatChartData(chartData, "MEDIUM"));
  const dataForLow = sortDataByDate(formatChartData(chartData, "LOW"));

  const allDates = [
    ...new Set(
      dataForHigh
        .map((item) => item?.date)
        .concat(
          dataForMedium.map((item) => item?.date),
          dataForLow.map((item) => item?.date)
        )
    ),
  ];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && label && payload && payload.length) {
      const values = Object.values(
        chartData?.find(
          (data) => payload[0]?.payload?.date === formatDate(data)
        ) || {}
      );

      return (
        <div className={styles.customTooltip}>
          {/* <p  className={styles.tooltipdate}>{`Date: ${label}`}</p> */}
          <div className={styles.tooltipSection}>
            <div className={styles.tooltipCategory}>
              <p className={styles.tooltipHeaderHigh}>HIGH</p>
              <p>{`IP: ${values[0]?.HIGH.IP}`}</p>
              <p>{`PNR: ${values[0]?.HIGH.PNR}`}</p>
              <p>{`USER: ${values[0]?.HIGH.USER}`}</p>
              <p>{`TOTAL: ${values[0]?.HIGH.TOTAL}`}</p>
            </div>
            <div className={styles.tooltipCategory}>
              <p className={styles.tooltipHeaderMedium}>MEDIUM</p>
              <p>{`IP: ${values[0]?.MEDIUM.IP}`}</p>
              <p>{`PNR: ${values[0]?.MEDIUM.PNR}`}</p>
              <p>{`USER: ${values[0]?.MEDIUM.USER}`}</p>
              <p>{`TOTAL: ${values[0]?.MEDIUM.TOTAL}`}</p>
            </div>
            <div className={styles.tooltipCategory}>
              <p className={styles.tooltipHeaderLow}>LOW</p>
              <p>{`IP: ${values[0]?.LOW.IP}`}</p>
              <p>{`PNR: ${values[0]?.LOW.PNR}`}</p>
              <p>{`USER: ${values[0]?.LOW.USER}`}</p>
              <p>{`TOTAL: ${values[0]?.LOW.TOTAL}`}</p>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  const handleDateRangeChange = (value) => {
    setDateRange(value);
  };

  const handleFilterChange = (value) => {
    // Handle filter change here
    console.log(value);
  };

      // const minimumDate = new Date();
      // minimumDate.setDate(minimumDate.getDate() - 7);


  return (
    <>
      <div className={styles.inputbarchartcontainer}>
        <div className={styles.inputbarchartSubcontainer}>
          <DateRangePicker
            value={dateRange}
            onChange={handleDateRangeChange}
            className={styles.FilterInputBarChart}
            cleanable={false}
            format="dd-MM-yyyy"
            placement="leftStart"
            // disabledDate={(date) => date < minimumDate}
          />
        </div>
      </div>

      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          width={500}
          height={300}
          data={allDates.map((date) => ({
            date,
            totalHigh:
              dataForHigh.find((item) => item?.date === date)?.total || 0,
            totalMedium:
              dataForMedium.find((item) => item?.date === date)?.total || 0,
            totalLow: dataForLow.find((item) => item?.date === date)?.total || 0,
          }))}
          margin={{ top: 5, right: 15, left: 5, bottom: 5 }}
          padding={{ left: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            type="category"
            style={{ color: "red" }}
            color="red"
          />  
          <YAxis
             type="number" 
             width={60}
             angle={-50} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Line
            type="monotone"
            dataKey="totalHigh"
            name="HIGH"
            stroke="red"
            activeDot={{ r: 8 }}
            strokeWidth={1.5}
          />
          <Line
            type="monotone"
            dataKey="totalMedium"
            name="MEDIUM"
            stroke="#4caf50"
            activeDot={{ r: 8 }}
            strokeWidth={1.5}
          />
          <Line
            type="monotone"
            dataKey="totalLow"
            name="LOW"
            stroke="#ffa600"
            activeDot={{ r: 8 }}
            strokeWidth={1.5}
          />
        </LineChart>
      </ResponsiveContainer>
    </>
  );
};

export default overviewBarCharts;
