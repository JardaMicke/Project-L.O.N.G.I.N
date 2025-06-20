import React from 'react';
import { useGIFIndicator } from '../hooks/useGIFIndicator';

/**
 * GIF type options for the ThinkingIndicator component
 */
type GIFType = 'thinking' | 'working';

/**
 * Props for the ThinkingIndicator component
 * @property {GIFType} [gifType='thinking'] - The type of GIF to display ('thinking' or 'working')
 * @property {boolean} [initiallyVisible=false] - Whether the GIF should be initially visible
 * @property {boolean} [showToggleButton=true] - Whether to show the toggle button (useful for development/testing)
 * @property {string} [className] - Additional CSS classes to apply to the container
 */
interface ThinkingIndicatorProps {
  gifType?: GIFType;
  initiallyVisible?: boolean;
  showToggleButton?: boolean;
  className?: string;
}

/**
 * A component that displays a "thinking" or "working" GIF indicator
 * to provide visual feedback during processing operations.
 *
 * Uses the useGIFIndicator hook to manage visibility state.
 *
 * @example
 * // Basic usage
 * <ThinkingIndicator />
 *
 * @example
 * // With custom type and initially visible
 * <ThinkingIndicator gifType="working" initiallyVisible={true} />
 *
 * @example
 * // Without toggle button (for production use)
 * <ThinkingIndicator showToggleButton={false} />
 */
export const ThinkingIndicator: React.FC<ThinkingIndicatorProps> = ({
  gifType = 'thinking',
  initiallyVisible = false,
  showToggleButton = true,
  className = '',
}) => {
  // Use the GIF indicator hook to manage visibility
  const { isVisible, toggle } = useGIFIndicator(initiallyVisible);

  // Determine which GIF to display based on the gifType prop
  const gifSrc = gifType === 'thinking' 
    ? '../assets/3LJU_V2.gif' 
    : '../assets/supawork-80adee47e1b141a88cd76bae2fa67845.gif';

  return (
    <div className={`flex flex-col items-center ${className}`}>
      {/* GIF container with conditional rendering */}
      <div className="w-24 h-24 flex items-center justify-center">
        {isVisible && (
          <img 
            src={gifSrc} 
            alt={gifType === 'thinking' ? 'Thinking...' : 'Working...'}
            className="max-w-full max-h-full"
          />
        )}
      </div>

      {/* Toggle button (optional) */}
      {showToggleButton && (
        <button
          onClick={toggle}
          className="mt-2 px-4 py-2 bg-black text-white border border-green-500 rounded hover:bg-gray-800 transition-colors"
        >
          {isVisible ? 'Hide' : 'Show'} Indicator
        </button>
      )}
    </div>
  );
};

export default ThinkingIndicator;
