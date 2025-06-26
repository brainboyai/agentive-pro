// frontend/src/components/widgets/WeatherWidget.tsx
import { widgetStyles } from './widgetStyles'; // Correctly import from the new shared file

export const WeatherWidget = ({ data }: { data: any }) => {
  const weatherData = data.api_data;

  if (!weatherData) {
    return (
      <div style={widgetStyles.container}>
        <h3>Weather for {data.location}</h3>
        <p>Fetching data...</p>
      </div>
    );
  }

  return (
    <div style={widgetStyles.container}>
      <h3>Weather in {weatherData.name}</h3>
      <div style={{ textAlign: 'center', fontSize: '24px', margin: '10px 0' }}>
        <img
          src={`http://openweathermap.org/img/wn/${weatherData.weather[0].icon}@2x.png`}
          alt={weatherData.weather[0].description}
        />
        <p>{Math.round(weatherData.main.temp)}°C</p>
      </div>
      <p style={{ textTransform: 'capitalize', textAlign: 'center' }}>
        {weatherData.weather[0].description}
      </p>
      <p style={{ textAlign: 'center', color: '#555' }}>
        Feels like: {Math.round(weatherData.main.feels_like)}°C
      </p>
    </div>
  );
};