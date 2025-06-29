// frontend/src/components/widgets/widgetStyles.ts
import React from 'react';

export const widgetStyles: { [key: string]: React.CSSProperties } = {
  container: {
    backgroundColor: '#fff',
    borderRadius: '8px',
    padding: '16px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    height: '100%',
  },
  mapPlaceholder: {
    height: '150px',
    backgroundColor: '#e9e9e9',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'column',
    borderRadius: '4px',
    textAlign: 'center',
    color: '#555',
  },
  listItemButton: {
    backgroundColor: '#f0f2f5',
    border: '1px solid #ddd',
    borderRadius: '4px',
    padding: '10px',
    textAlign: 'left',
    cursor: 'pointer',
    fontSize: '14px',
    width: '100%'
  }
};