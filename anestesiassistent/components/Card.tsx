
import React from 'react';

interface CardProps {
    children: React.ReactNode;
    className?: string;
    title?: string;
}

export const Card: React.FC<CardProps> = ({ children, className = '', title }) => {
    return (
        <div className={`bg-slate-800 border border-slate-700 rounded-xl shadow-lg p-6 ${className}`}>
            {title && <h2 className="text-xl font-bold text-cyan-400 mb-4">{title}</h2>}
            {children}
        </div>
    );
};
