import { useState } from 'react';

/**
 * @typedef {Object} GIFIndicatorControls
 * @property {boolean} isVisible - The current visibility state of the GIF.
 * @property {() => void} show - Function to set the GIF visibility to true.
 * @property {() => void} hide - Function to set the GIF visibility to false.
 * @property {() => void} toggle - Function to toggle the GIF visibility.
 */

/**
 * Custom React hook to manage the visibility state of a GIF indicator.
 * This hook provides functions to show, hide, and toggle the visibility,
 * along with the current visibility state.
 *
 * @param {boolean} [initialState=false] - The initial visibility state of the GIF. Defaults to false.
 * @returns {GIFIndicatorControls} An object containing the visibility state and control functions.
 *
 * @example
 * const { isVisible, show, hide, toggle } = useGIFIndicator();
 *
 * return (
 *   <div>
 *     <button onClick={toggle}>Toggle GIF</button>
 *     {isVisible && <img src="/path/to/thinking.gif" alt="Thinking" />}
 *   </div>
 * );
 */
export const useGIFIndicator = (initialState: boolean = false) => {
  const [isVisible, setIsVisible] = useState<boolean>(initialState);

  /**
   * Sets the GIF visibility to true.
   */
  const show = () => setIsVisible(true);

  /**
   * Sets the GIF visibility to false.
   */
  const hide = () => setIsVisible(false);

  /**
   * Toggles the GIF visibility between true and false.
   */
  const toggle = () => setIsVisible(prev => !prev);

  return {
    isVisible,
    show,
    hide,
    toggle,
  };
};
