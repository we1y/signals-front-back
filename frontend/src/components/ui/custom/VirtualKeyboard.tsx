import { Delete } from 'lucide-react';
import React from 'react';

interface VirtualKeyboardProps {
  onKeyPress: (key: string) => void;
  onDelete: () => void;
}

const VirtualKeyboard: React.FC<VirtualKeyboardProps> = ({ onKeyPress, onDelete }) => {
  const keys = '0123456789'.split('');

  return (
    <>
      <div className="grid grid-cols-3 grid-rows-3 font-bold">
        {keys.map((key) => (
          <button key={key} onClick={() => onKeyPress(key)} className='bg-primary p-1 m-1 rounded-xl'>
            {key}
          </button>
        ))}
        <button onClick={onDelete} className='bg-primary p-1 m-1 rounded-xl flex justify-center'>
            <Delete />
        </button>
      </div>
    </>
  );
};

export default VirtualKeyboard;