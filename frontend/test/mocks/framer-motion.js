// Renders motion.* as the plain element, dropping animation-only props.
const React = require("react");

const MOTION_PROPS = new Set([
  "initial", "animate", "exit", "transition", "variants", "custom", "layout", "layoutId",
  "whileHover", "whileTap", "whileFocus", "whileInView", "whileDrag", "viewport",
  "drag", "dragConstraints", "dragElastic", "onAnimationStart", "onAnimationComplete",
]);

const cache = {};
const motion = new Proxy({}, {
  get(_, tag) {
    if (!cache[tag]) {
      cache[tag] = React.forwardRef(({ children, ...props }, ref) => {
        const domProps = {};
        for (const key of Object.keys(props)) if (!MOTION_PROPS.has(key)) domProps[key] = props[key];
        return React.createElement(tag, { ...domProps, ref }, children);
      });
    }
    return cache[tag];
  },
});

module.exports = {
  motion,
  AnimatePresence: ({ children }) => React.createElement(React.Fragment, null, children),
  useAnimation: () => ({ start: () => Promise.resolve(), stop: () => {} }),
  useMotionValue: (v) => ({ get: () => v, set: () => {}, on: () => () => {} }),
  useSpring: (v) => v,
  useTransform: () => 0,
  useInView: () => true,
  useReducedMotion: () => true,
};
