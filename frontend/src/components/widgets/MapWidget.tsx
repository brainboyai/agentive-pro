// frontend/src/components/widgets/MapWidget.tsx
import { widgetStyles } from './widgetStyles'; // Import from the new shared file

export const MapWidget = ({ data }: { data: any }) => (
  <div style={widgetStyles.container}>
    <h3>Map of {data.location}</h3>
    <div style={widgetStyles.mapPlaceholder}>
      <p>A map would be rendered here.</p>
      <p>Details: {data.details}</p>
    </div>
  </div>
);