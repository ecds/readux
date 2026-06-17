// Stub for react-draggable — replaces the draggable editor popup behavior with a
// static wrapper. react-draggable 4.x calls ReactDOM.findDOMNode which is absent
// from the React 18 production bundle, so we drop it rather than polyfill.
import React from 'react';

const Draggable = ({ children }) => children;
Draggable.DraggableCore = ({ children }) => children;

export default Draggable;
export const DraggableCore = ({ children }) => children;
