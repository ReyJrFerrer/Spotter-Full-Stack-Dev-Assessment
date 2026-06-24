import React, { useState, useRef, useEffect, useCallback } from 'react';

interface AutocompleteResult {
  label: string;
  city: string;
  state: string;
  lat: number;
  lng: number;
}

interface Props {
  id: string;
  label: string;
  icon: React.ReactNode;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  apiUrl: string;
  staticOptions?: string[];
}

export default function LocationAutocomplete({ id, label, icon, value, onChange, placeholder, apiUrl, staticOptions }: Props) {
  const [inputValue, setInputValue] = useState(value);
  const [results, setResults] = useState<AutocompleteResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();
  const requestIdRef = useRef(0);

  const isApiSearch = inputValue.length >= 2;

  const fetchResults = useCallback(async (query: string) => {
    const currentId = ++requestIdRef.current;
    setIsLoading(true);
    setError(null);
    try {
      const url = `${apiUrl}?q=${encodeURIComponent(query)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Autocomplete request failed');
      const data: AutocompleteResult[] = await res.json();
      if (currentId === requestIdRef.current) {
        setResults(data ?? []);
        setIsLoading(false);
      }
    } catch {
      if (currentId === requestIdRef.current) {
        setError('Could not fetch cities');
        setResults([]);
        setIsLoading(false);
      }
    }
  }, [apiUrl]);

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [isOpen]);

  useEffect(() => {
    setHighlightIndex(-1);
  }, [results.length]);

  const displayItems = isApiSearch ? results.map((r) => r.label) : (staticOptions ?? []);
  const displayCount = displayItems.length;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setInputValue(val);
    onChange(val);

    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (val.length < 2) {
      setResults([]);
      setIsLoading(false);
      if (staticOptions && staticOptions.length > 0) {
        setIsOpen(true);
      } else {
        setIsOpen(false);
      }
      return;
    }

    setIsOpen(true);
    debounceRef.current = setTimeout(() => fetchResults(val), 300);
  };

  const selectLabel = (label: string) => {
    onChange(label);
    setInputValue(label);
    setIsOpen(false);
    setHighlightIndex(-1);
    setResults([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        setIsOpen(true);
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightIndex((prev) => (prev < displayCount - 1 ? prev + 1 : 0));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightIndex((prev) => (prev > 0 ? prev - 1 : displayCount - 1));
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightIndex >= 0 && highlightIndex < displayCount) {
          selectLabel(displayItems[highlightIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setHighlightIndex(-1);
        break;
    }
  };

  useEffect(() => {
    if (highlightIndex >= 0 && listRef.current) {
      const item = listRef.current.children[highlightIndex] as HTMLElement | undefined;
      item?.scrollIntoView({ block: 'nearest' });
    }
  }, [highlightIndex]);

  return (
    <div ref={wrapperRef} className="relative">
      <label htmlFor={id} className="text-[10px] font-bold text-[#1A1A1A] uppercase tracking-widest block mb-1">
        {label}
      </label>
      <div className="relative">
        <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          {icon}
        </span>
        <input
          ref={inputRef}
          id={id}
          type="text"
          required
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => {
            if (isApiSearch) {
              setIsOpen(true);
              if (results.length === 0 && !isLoading) {
                fetchResults(inputValue);
              }
            } else if (staticOptions && staticOptions.length > 0) {
              setIsOpen(true);
            }
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          autoComplete="off"
          className="w-full pl-10 pr-3 py-2.5 text-sm bg-[#F4F1ED]/40 hover:bg-[#F4F1ED]/65 focus:bg-white border border-[#1A1A1A] text-[#1A1A1A] font-medium rounded-none outline-none transition-all focus:ring-1 focus:ring-[#1A1A1A]"
        />
        {isLoading && (
          <span className="absolute inset-y-0 right-3 flex items-center pointer-events-none">
            <svg className="animate-spin h-4 w-4 text-[#1A1A1A]/40" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </span>
        )}
      </div>

      {isOpen && displayCount > 0 && (
        <ul
          ref={listRef}
          className="absolute z-50 mt-1 w-full bg-white border border-[#1A1A1A] shadow-[4px_4px_0px_#1A1A1A] max-h-52 overflow-y-auto"
        >
          {displayItems.map((item, i) => (
            <li
              key={`${item}-${i}`}
              role="option"
              aria-selected={i === highlightIndex}
              onMouseDown={() => selectLabel(item)}
              onMouseEnter={() => setHighlightIndex(i)}
              className={`px-3 py-2 text-sm cursor-pointer transition-colors ${
                i === highlightIndex
                  ? 'bg-[#1A1A1A] text-white'
                  : 'bg-white text-[#1A1A1A] hover:bg-[#E8E4DF]'
              }`}
            >
              {item}
            </li>
          ))}
        </ul>
      )}

      {isOpen && isApiSearch && displayCount === 0 && isLoading && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-[#1A1A1A] shadow-[4px_4px_0px_#1A1A1A] px-3 py-2 text-sm text-[#1A1A1A]/60 flex items-center gap-2">
          <svg className="animate-spin h-3.5 w-3.5 text-[#1A1A1A]/40" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span>Searching US cities...</span>
        </div>
      )}

      {isOpen && isApiSearch && displayCount === 0 && !isLoading && !error && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-[#1A1A1A] shadow-[4px_4px_0px_#1A1A1A] px-3 py-2 text-sm text-[#1A1A1A]/60">
          No matching US city found
        </div>
      )}

      {isOpen && error && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-[#1A1A1A] shadow-[4px_4px_0px_#1A1A1A] px-3 py-2 text-sm text-red-600">
          {error}
        </div>
      )}
    </div>
  );
}
