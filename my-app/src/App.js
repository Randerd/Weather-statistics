// import sunny from './img/sunny.png';
// import cloudy from './img/cloudy.png';
// import snowy from './img/snowy.png';
// import rainy from './img/rainy.png';
// import all from './img/all.png';
import graph from './img/graph.png'
import eqBlue from './img/eqBlue.png'
import eqRed from './img/eqRed.png'
import eqGreen from './img/eqGreen.png'
import conditionIndex from './img/conditionIndex.png'
import React, {useEffect, useState} from 'react';
import './App.css';

function getColor(value) {
  if (value === '-'){
    return 'white'
  }
  return ["hsl(", value, ",100%,50%)"].join("");
}

function Provider(props){
  // console.log(props)
  const {name, stats} = props;
  return <div className='cell'>
      <h2>{name} 'logo'</h2>
      <div>
        {stats.map((stat, idx) => (
          <p style={{color: getColor(stat), fontWeight: 'bold'}} key={idx}>{stat}%</p>
        ))}
      </div>
    </div>
}


function App() {
  const [providers, setProviders] = useState([
      {name: "Accu Weather", stats:[87.58,88.34,75.45,64.14,83.65,55.78,46.80,56.89,49.33,21.21]}, 
      {name: "Open Weather", stats:[95.23,93.84,72.51,84.67,65.83,78.21,68.97,32.11,54.55,65.41]}, 
      {name: "Weather API", stats:[93.45,84.85,91.42,85.39,76.76,54.33,42.87,61.59,39.81,31.02]}, 
  ])
  // const providers = ['Accu Weather', 'Open Weather', 'Weather API']
  const locations = [
    {label: "Toronto", value: 'Toronto'},
    {label: "Innisfil", value: 'Innisfil'},
    {label: "Kingston", value: 'Kingston'}]
  // let Acc_data = []
  // const [Acc_data, setAcc_data] = useState([])
  // let Acc_data = [
  //   [83.65, 84.44, 86.37, 84.53, 84.8, 85.25, 84.61, 84.82, 85.85, 85.16, 85.23, 84.15],
  //   [91.57, 92.11, 91.67, 92.49, 92.42, 90.5, 90.21, 89.36, 89.44, 89.27, 89.02, 89.82],
  //   [53.65, 51.82, 53.08, 53.3, 53.56, 54.9, 55.09, 54.81, 55.38, 56.27, 56.76, 55.76],
  //   [93.36, 96.99, 94.95, 95.19, 95.62, 95.62, 95.61, 95.56, 95.58, 95.56, 95.54, 94.98],
  //   [96.84, 93.33, 92.05, 94.4, 96.43, 95.96, 94.97, 95.03, 94.94, 94.9, 94.52, 93.36],
  //   [99.19, 99.05, 98.58, 98.6, 99.59, 99.55, 98.87, 98.45, 98.39, 98.31, 98.26, 98.25],
  //   [76.55, 75.8, 75.24, 75.62, 75.69, 75.65, 75.67, 75.67, 75.73, 75.83, 78.53, 78.74],
  //   ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
  //   ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-']]
  const [Acc_data, setAcc_data] = useState([
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-']])
  const [location, setLocation] = useState('Toronto')  
  const [sinceDate, setSinceDate] = useState(new Date());
  const [condition, setCondition] = useState('all')
  const [infoHovering, setInfoHovering] = useState(false)
  
  useEffect(() => {
      fetch(' https://0yl27fj30f.execute-api.ca-central-1.amazonaws.com/default/Get-Accuracy')
        .then((response) => response.json())
        .then((data) => {setAcc_data(data)})
      
    }, [])

    useEffect(() => {
      changeData()
    }, [location, Acc_data])


  const changeData = () => {
    switch(location){
      case 'Toronto':
        console.log('change Toronto')
        setProviders([
          {name: "Weather API", stats: Acc_data[0]},
          {name: "Open Weather", stats: Acc_data[3]}, 
          {name: "Accu Weather", stats: Acc_data[6]}, 
        ])
        break
      case 'Kingston':
          console.log('change Kingston')
          setProviders([
            {name: "Weather API", stats: Acc_data[1]},
            {name: "Open Weather", stats: Acc_data[4]}, 
            {name: "Accu Weather", stats: Acc_data[7]}, 
        ])
        break
      case 'Innisfil':
        console.log('change Innisfil')
        setProviders([
          {name: "Weather API", stats: Acc_data[2]},
          {name: "Open Weather", stats: Acc_data[5]}, 
          {name: "Accu Weather", stats: Acc_data[8]}, 
        ])
        break
    }
  }
  const getOpacity = () =>{
    return infoHovering === true ? 1 : 0
  }
  const getVisibility = () =>{
    return infoHovering === true ? 'visible' : 'hidden'
  }

  const OnConditionChange = (event) => {
    const value = event.target.value
    setCondition(value)
    console.log(value)
  }

  const onLocationChange = (event) => {
    const value = event.target.value
    setLocation(value)
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
            <h4>Anylitics</h4>
            {statisitcs.map((stat, idx) => (
              <p key={idx}>{stat}</p>
            ))}

          </div>
          {providers.map((provider, idx) => (
            <Provider key={idx} name={provider.name} stats={provider.stats}/>
            // <div key={idx} className='cell'>{provider}</div>
          ))}
        </section>
        <section className='bot'>
          {/* <div className='conditions'>
            <h3> Conditions:</h3>
            <label className='radios' >
              <input type="radio" id="all" value="all" name="condition" checked={condition === 'all'} onChange={OnConditionChange.bind(this)}/>
              <img alt='all' src={all}/>
            </label>
            <label className='radios'>
              <input type="radio" id="sunny" value="sunny" name="condition" checked={condition === 'sunny'} onChange={OnConditionChange.bind(this)}/>
              <img alt='sunny' src={sunny}/>
            </label>
            <label className='radios'>
              <input type="radio" id="cloudy" value="cloudy" name="condition" checked={condition === 'cloudy'} onChange={OnConditionChange.bind(this)}/>
              <img alt='cloudy' src={cloudy}/>
            </label>
            <label className='radios'>
              <input type="radio" id="rainy" value="rainy" name="condition" checked={condition === 'rainy'} onChange={OnConditionChange.bind(this)}/>
              <img  alt='rainy' src={rainy}/>
              </label>
            <label className='radios'>
              <input type="radio" id="snowy" value="snowy" name="condition" checked={condition === 'snowy'} onChange={OnConditionChange.bind(this)}/>
              <img  alt='snowy' src={snowy}/>
            </label>
          </div> */}
          <div className='date'>
            <h3> Time period</h3>
            <p>Since: {formatAMPM(sinceDate)} - {sinceDate.toLocaleDateString()}</p>
          </div>
          <div className='location'>
            <h3> Location </h3>
            <select value={location} onChange={onLocationChange}>
              {locations.map((loc, idx) => (
                <option key={idx} value={loc.value}>{loc.label}</option>
              ))}
            </select>

          </div>
          <div className='info'
            onMouseOver={()=>{setInfoHovering(true)}}
            onMouseOut={()=>{setInfoHovering(false)}}
          >i</div>

        </section>
      </div>
      <div className='infoScreen' style={{visibility: getVisibility(), opacity: getOpacity()}}>
        <h2>How statisitcs are calculated</h2>
        <img id='graph' alt='graph' src={graph} style={{width: '60%'}}/> 
        <div className='disc'>
          <img alt='f(x)' src={eqBlue} style={{width:'80%', background:'#999999'}}/>
          <p>Final value for the given prediction</p>
          <img alt='c(a)' src={eqRed} style={{width:'70%', background:'#999999'}}/>
          <p>Where a is the Difference in condition between the current and expected condition</p> 
          <img alt='t(b)' src={eqGreen} style={{width:'70%', background:'#999999'}}/>
          <p>Where b is the Difference in temperature between current and expected temperature</p>
        </div>
        <div className='example'> 
          <h4>Example:</h4>  
          <p>Current conditions: Sunny, 15C</p>
          <p>Expected conditions: partly cloudy, 18C</p>
          <p>Condition index off: 1, Temp diff: 3 </p>
          <p>Prediction value: 64.23%</p>
        </div>
        <div className='conditionIndex'> 
            <h4 style={{marginBottom:'0'}}> Condition Index </h4>
            <img alt='condition index' src={conditionIndex} />
            {/* <div className='test'></div> */}
        </div>
      </div>
    </div>
  );
}

export default App;
