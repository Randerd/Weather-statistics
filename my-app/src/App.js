import AccuWeather from './img/AccuWeather.png'
import OpenWeather from './img/OpenWeather.png'
import weatherAPI from './img/weatherAPI.png'
import React, {useEffect, useState} from 'react';
import './App.css';
import Select from 'react-select'

function getColor(value) {
  if (value === '-'){
    return 'white'
  }
  return ["hsl(", value, ",100%,50%)"].join("");
}

const links = {'Accu Weather': 'https://www.accuweather.com/',
              'Open Weather': 'https://openweathermap.org/',
              'Weather API': 'https://www.weatherapi.com/weather/'}

function Provider(props){
  const {logo,name, stats} = props;
  return <div className='cell'>
      <img src={logo} alt={name+'logo'} onClick={()=>window.open(links[name])}/>
      {/* <h2>{name} 'logo'</h2> */}
      <div>
        {stats.map(([stat,count], idx) => (
          <div style={{margin: '16px 0 16px 0'}} key={idx}>
            <span style={{color: getColor(stat), fontWeight: 'bold'}}>{stat}%</span>
            <span style={{marginLeft: '5px', fontSize: '11px', color: '#CCCCCC'}}>{count}</span>
          </div>
        ))}
      </div>
    </div>
}


function App() {
  const [providers, setProviders] = useState([
      {logo: AccuWeather, name: "Accu Weather", stats:[[87.82, 52], [88.2, 52], [89.2, 52], [88.29,52], [88.68,52], [88.34,52], [87.16,52], [87.2,52], [87.69,52], [86.63,52], [86.51,52], [85.66,52]]}, 
      {logo: OpenWeather, name: "Open Weather", stats:[[87.82, 52], [88.2, 52], [89.2, 52], [88.29,52], [88.68,52], [88.34,52], [87.16,52], [87.2,52], [87.69,52], [86.63,52], [86.51,52], [85.66,52]]}, 
      {logo: weatherAPI, name: "Weather API", stats:[[87.82, 52], [88.2, 52], [89.2, 52], [88.29,52], [88.68,52], [88.34,52], [87.16,52], [87.2,52], [87.69,52], [86.63,52], [86.51,52], [85.66,52]]}, 
  ])
  const locations = [
    {label: "Toronto", value: 'Toronto'},
    {label: "Innisfil", value: 'Innisfil'},
    {label: "Kingston", value: 'Kingston'}]

  const [Acc_data, setAcc_data] = useState([
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-']
  ])
  const [location, setLocation] = useState({label: "Toronto", value: 'Toronto'})  
  // const [sinceDate, setSinceDate] = useState(new Date(2023,11,8,0));
  const sinceDate = new Date(2023,11,5,12)

  const customStyles = {
    option: (defaultStyles, state) => ({
      ...defaultStyles,
      color: state.isSelected ? "#555555" : "#ffffff",
      backgroundColor: state.isSelected ? "#FFFFFF" : "#555555",
      // height: '35px',
    }),

    control: (defaultStyles) => ({
      ...defaultStyles,
      backgroundColor: "#555555",
      padding: "2px",
      border: "none",
      boxShadow: "none",
    }),
    singleValue: (defaultStyles) => ({ ...defaultStyles, color: "#fff" }),
  };

  useEffect(() => {
    fetch('https://5g6zpwtxll.execute-api.ca-central-1.amazonaws.com/default/Get-Accuracy')
        .then((response) => response.json())
        .then((data) => {setAcc_data(data)})
    }, [])

    useEffect(() => {
      changeData()
    }, [location, Acc_data])


  const changeData = () => {
    switch(location.label){
      case 'Toronto':
        setProviders([
          {logo: weatherAPI, name: "Weather API", stats: Acc_data[0]},
          {logo: OpenWeather, name: "Open Weather", stats: Acc_data[3]}, 
          {logo: AccuWeather, name: "Accu Weather", stats: Acc_data[6]}, 
        ])
        break
      case 'Kingston':
          setProviders([
            {logo: weatherAPI,name: "Weather API", stats: Acc_data[1]},
            {logo: OpenWeather,name: "Open Weather", stats: Acc_data[4]}, 
            {logo: AccuWeather,name: "Accu Weather", stats: Acc_data[7]}, 
        ])
        break
      case 'Innisfil':
        setProviders([
          {logo: weatherAPI,name: "Weather API", stats: Acc_data[2]},
          {logo: OpenWeather,name: "Open Weather", stats: Acc_data[5]}, 
          {logo: AccuWeather,name: "Accu Weather", stats: Acc_data[8]}, 
        ])
        break
      default:
        setProviders([
          {logo: weatherAPI,name: "Weather API", stats: Acc_data[0]},
          {logo: OpenWeather,name: "Open Weather", stats: Acc_data[3]}, 
          {logo: AccuWeather,name: "Accu Weather", stats: Acc_data[6]}, 
        ])
        break
    }
  }

  function formatAMPM(date) {
    var hours = date.getHours();
    var ampm = hours >= 12 ? 'pm' : 'am';
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'
    var strTime = hours + ' ' + ampm;
    return strTime;
  }

  const statisitcs = ['1 Hour', '2 Hour', '3 Hour', '4 Hour', '5 Hour', '6 Hour', '7 Hour', '8 Hour', '9 Hour', '10 Hour','11 Hour', '12 Hour']
  // const statisitcs = ['1 Hour', '2 Hour', '3 Hour', '6 Hour', '12 Hour', '1 Day', '2 Day', '3 Day', '4 Day', '5 Day']
  return (
    <div className='App'>
      <div className='header'>Weather Statistics</div>
      <div className="container">
        <section className='cells'>
          <div className='cell'>
            <h4>Analytics</h4>
            {statisitcs.map((stat, idx) => (
              <p className='text' key={idx}>{stat}</p>
            ))}

          </div>
          {providers.map((provider, idx) => (
            <Provider key={idx} logo={provider.logo} name={provider.name} stats={provider.stats}/>
          ))}
        </section>
        <section className='bot'>
          <div className='date'>
            <h3> Time period:</h3>
            <p>Since: {sinceDate.toISOString().substring(0,10)} {formatAMPM(sinceDate)}</p>
          </div>
          <div>
            <h3> Location: </h3>
            <Select
              className='select'
              defaultValue={location}
              onChange={setLocation}
              options={locations}
              styles={customStyles}
            />
          </div>
          <div className='info'
            onClick={() => window.open("https://github.com/Randerd/Weather-statistics/tree/main")}>
              i
          </div>

        </section>
      </div>
    </div>
  );
}

export default App;
