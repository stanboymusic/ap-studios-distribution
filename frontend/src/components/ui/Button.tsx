import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  children: React.ReactNode;
}

export function Button({ variant = 'primary', children, className = "", ...props }: ButtonProps) {
  const variants = {
    primary: 'btn-primary',
    secondary: 'btn-ghost',
    outline: 'btn-ghost',
    ghost: 'btn-ghost'
  };

  return (
    <button 
      className={`${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
