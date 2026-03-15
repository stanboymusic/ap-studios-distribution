import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  children: React.ReactNode;
}

export function Button({ variant = 'primary', children, className = "", ...props }: ButtonProps) {
  const variants = {
    primary: 'bg-[#1B4079] hover:bg-[#16345F] text-white',
    secondary: 'bg-[#4D7C8A] hover:bg-[#3E636E] text-white',
    outline: 'border border-gray-200 hover:bg-gray-50 text-gray-700',
    ghost: 'hover:bg-gray-100 text-gray-600'
  };

  return (
    <button 
      className={`px-4 py-2 rounded-xl font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50 ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
