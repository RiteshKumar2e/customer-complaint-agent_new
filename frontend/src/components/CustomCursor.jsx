import { useEffect, useState } from "react";
import { motion, useSpring } from "framer-motion";

export default function CustomCursor() {
    const [isHovering, setIsHovering] = useState(false);

    const springConfig = { damping: 25, stiffness: 200 };
    const cursorX = useSpring(0, springConfig);
    const cursorY = useSpring(0, springConfig);

    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        setIsVisible(window.matchMedia("(pointer: fine)").matches);

        const handleMouseMove = (e) => {
            cursorX.set(e.clientX);
            cursorY.set(e.clientY);
        };

        const handleHover = (e) => {
            const isClickable = e.target.closest('button, a, input, .auth-link, .password-toggle');
            setIsHovering(!!isClickable);
        };

        if (window.matchMedia("(pointer: fine)").matches) {
            window.addEventListener("mousemove", handleMouseMove);
            window.addEventListener("mouseover", handleHover);
        }

        return () => {
            window.removeEventListener("mousemove", handleMouseMove);
            window.removeEventListener("mouseover", handleHover);
        };
    }, [cursorX, cursorY]);

    if (!isVisible) return null;

    return (
        <>
            <motion.div
                className="custom-cursor-main"
                style={{
                    translateX: cursorX,
                    translateY: cursorY,
                }}
                animate={{
                    scale: isHovering ? 2.5 : 1,
                    backgroundColor: isHovering ? "rgba(139, 92, 246, 0.3)" : "rgba(139, 92, 246, 0.8)",
                }}
            />
            <motion.div
                className="custom-cursor-outline"
                style={{
                    translateX: cursorX,
                    translateY: cursorY,
                }}
                animate={{
                    scale: isHovering ? 1.5 : 1,
                    opacity: isHovering ? 0 : 1,
                }}
                transition={{ type: "spring", damping: 30, stiffness: 150 }}
            />
        </>
    );
}
