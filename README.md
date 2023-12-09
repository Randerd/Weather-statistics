# GitHub Pages link
https://randerd.github.io/Weather-statistics/

# Reasoning
Built to settle a debate with some friends during the summer about what weather provider is best to use 😄.   
Unfortunately, not the end result I wished as most of the providers in the debate had no available APIs

# Description
_Middle-tier_ for "Weather Statistics" application.   
Calculates accuracy scores for weather providers based on how accurate their APIs forecasts are.  

Uses AWS Lambda to collect and analyze data, as well to send data as API endpoint  
&ensp;Lambdas scheduled to run on an hourly bases using AWS EventBridge schedules   
&ensp;Data stored using AWS DynamoDB, a NoSQL database*

*Originally built using AWS RDS but transitioned due to costs 😑

## Functions

### Get-Forecast
For each provider, this function collects 12 hour forecast and current weather data to store in DynamoDB keyed on date and time collected. 

### Get-Statistics 
For each table (API provider, location), reads the current weather values and compares them with what was previously forecasted for this time (up to 12 hours). Comparison/accuracy scores* are added to a running average stored in the database.  

*Custom scoring formula

Temperature: Measured in C°  
Condition: Converted to condition index value

<font size=4>Condition Index:  </font>
| Category:    | Clear Skies    | Partially cloudy    | Cloudy    | Rain/Snow    | Storms or heavy fall    |
| -------------| ---------------| --------------------| ----------| -------------| ------------------------|
| Index Value:  | 1              | 2                   | 3         | 4            | 5                       |
<!-- | pic? | pic?| pic? | pic? | pic? |    -->

<font size=4> How the accuracy score is calculated:  </font>  
t = |difference| in temperature between the current and forecasted values  
Temperature difference score =>  ${\color{#dd4444} T(t) = 2^{t\over 7} - 1}$   
c = |difference| in condition index between the current and forecasted values   
Condition index difference score => $\color{#44DD44}C(c) = 2^{c\over 3} - 1$  
Accuracy score => $\color{#44dddd} A(c,t) = e^{-[T(t) + C(c)]^2}$ $ \times 100$ 

<font size=3> Visualization:  </font>  
<img src="imgs/geogebra.png" alt="visualization" style="width:auto; max-width: 650px"/>

<font size=3>Example:</font>  
Current forecast being accessed: 4-hour forecast   
Current weather: 2023-06-23T20, 21.3° Cloudy  
Forecast Weather: 2023-03-23T14, 20.8° Partially Cloudy  

$t = | 21.3 - 20.8 | = 0.5  $  
$T(t) = 2^{0.5\over 7} - 1 = 0.050756...$   
$c = | 3 - 2 | = 1  $  
$C(c) = 2^{1\over 3} - 1 = 0.259921...$   
$A(c,t) = e^{-[T(t) + C(c)]^2} \times 100 = e^{-[0.0507... + 0.2599...]^2} \times 100 = 90.80%$  
∴ The associated 4-hour accuracy score given for the date 2023-03-23T14 is  $\color{#44DD44}90.80$%

Note: Bell function and exponentials were chosen so the further from the true value, the more it _scales_ down
### Get-Accuracy
Reads and returns accuracy data from each table in database into an array  
*Used as API endpoint to retrieve data from database

### Create-Tables
3 functions   
&ensp;&ensp;&ensp;- Create Tables  
&ensp;&ensp;&ensp;- Delete Tables  
&ensp;&ensp;&ensp;- Clear Tables  
&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;- Faster and easier to delete -> create all tables again 

*Primarily used for testing purposes 

## Schedulers
#### run-on-15
Scheduler to run on the 15th minute of every hour to call the _Get-Forecast_ Lambda.  
*Ran on 15th minute to allow APIs time to update. If not up-to-date when called, data is ignored
#### run-on-30
Scheduler to run on the 30th minute of every hour to call the _Get-Statistics_ Lambda.    
*Ran on 30th minute to give time for _Get-Forcast_ to execute
## Database
7 Tables, one for each (provider, location) pair   
```
Weather_API_toronto     Open_Weather_toronto    Accu_Weather_toronto
Weather_API_kingston    Open_Weather_kingston
Weather_API_innisfil    Open_Weather_innisfil
```

Each table indexed with the following index scheme
| Date (_Primary_)   | cur    | f1    | f2    | f3    | ...    | f11    | f12    | forecast    |
|--------------------|--------|-------|-------|-------|--------|--------|--------|-------------|

Each table has one item for keeping track of the average forecast for the table. This is so the average forecast can easily be retrieved instead of constantly calculated every time. 

## Possible future plans
- More weather providers
- More forecast points (1 day, 2 days, etc.)
- Variable date range
- More complex scoring formula  
- - More variables per data point (precipitation change, humidity, etc.)

## Limitations
- Accu Weather API calls limit
- - Accu Weather  has a 50 calls per day limit on their API free tier**. This is just enough to do 2 calls per hour (48 total calls) for the current and 12 hour forecast each hour.  
- - This will also affect Open Weather once I lose the student API tier
- Providers
- - I initially wanted to utilize more common weather providers, specifically those apart of the initial debate, such as the Weather Network and Weather Channel, but they have no available APIs

**Weather APIs are pretty expensive, especially when you would be paying for 3-4 a month 😬

