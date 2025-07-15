import { useState, useRef, useEffect } from "react";

interface DraggableContainerProps {
  children: React.ReactNode;
  className?: string;
  defaultPosition?: { x: number; y: number };
  isDraggable?: boolean;
}

const DraggableContainer = ({
  children,
  className = "",
  defaultPosition = { x: 0, y: 0 },
  isDraggable = false,
}: DraggableContainerProps) => {
  const [position, setPosition] = useState(defaultPosition);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!isDraggable) return;

    setIsDragging(true);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    });
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !isDraggable) return;

      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, dragStart, isDraggable]);

  const style = isDraggable
    ? {
        transform: `translate(${position.x}px, ${position.y}px)`,
        cursor: isDragging ? "grabbing" : "grab",
        position: "relative" as const,
      }
    : {};

  return (
    <div
      ref={containerRef}
      className={className}
      style={style}
      onMouseDown={handleMouseDown}
    >
      {children}
    </div>
  );
};

export default DraggableContainer;
