// frontend/src/components/widgets/PlanWidget.tsx
import { widgetStyles } from './widgetStyles';

type PlanStep = {
  title: string;
  description: string;
};

type PlanWidgetProps = {
  steps: PlanStep[];
  onStepClick: (stepTitle: string) => void;
};

export const PlanWidget = ({ steps, onStepClick }: PlanWidgetProps) => (
  <div style={widgetStyles.container}>
    <h3>Here is the plan I generated:</h3>
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {steps.map((step, index) => (
        <button 
          key={index} 
          style={widgetStyles.listItemButton}
          onClick={() => onStepClick(step.title)}
          title={step.description} // Show description on hover
        >
          <strong>{step.title}</strong>
          <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#555' }}>{step.description}</p>
        </button>
      ))}
    </div>
  </div>
);