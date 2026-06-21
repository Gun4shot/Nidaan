'use client';

import { useState, useRef, useEffect } from 'react';
import type { PatientInfo } from '@/hooks/useSessions';

interface PatientIntakeProps {
  onSubmit: (patient: PatientInfo) => void;
  onCancel: () => void;
}

export default function PatientIntake({ onSubmit, onCancel }: PatientIntakeProps) {
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    nameRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !age.trim() || !gender) return;
    onSubmit({ name: name.trim(), age: age.trim(), gender });
  };

  const isValid = name.trim() && age.trim() && gender;

  return (
    <div className="intake-overlay">
      <div className="intake-modal">
        <div className="intake-header">
          <span className="material-symbols-outlined intake-icon">person_add</span>
          <h2 className="intake-title">Patient Information</h2>
          <p className="intake-subtitle">Enter details for this consultation session.</p>
        </div>

        <form className="intake-form" onSubmit={handleSubmit}>
          <div className="intake-field">
            <label className="intake-label">Full Name</label>
            <input
              ref={nameRef}
              type="text"
              className="intake-input"
              placeholder="e.g. Ram Bahadur Thapa"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="intake-row">
            <div className="intake-field">
              <label className="intake-label">Age</label>
              <input
                type="number"
                className="intake-input"
                placeholder="e.g. 34"
                min="0"
                max="150"
                value={age}
                onChange={(e) => setAge(e.target.value)}
              />
            </div>

            <div className="intake-field">
              <label className="intake-label">Gender</label>
              <div className="intake-gender">
                {['Male', 'Female', 'Other'].map((g) => (
                  <button
                    key={g}
                    type="button"
                    className={`intake-gender-btn ${gender === g ? 'intake-gender-btn--active' : ''}`}
                    onClick={() => setGender(g)}
                  >
                    {g}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="intake-actions">
            <button type="button" className="intake-cancel" onClick={onCancel}>
              Skip
            </button>
            <button type="submit" className="intake-submit" disabled={!isValid}>
              Start Session
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
