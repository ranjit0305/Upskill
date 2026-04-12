import React from 'react';
import { CheckCircle2, Circle, Clock, ArrowRight, Star, Trophy, Target } from 'lucide-react';
import './Roadmap.css';

const RoadmapTree = ({ stages = [] }) => {
    // Default stages if none provided
    const defaultStages = [
        { id: '1', title: 'Aptitude & Logical', status: 'completed', description: 'Master number systems, probability, and logical reasoning patterns.' },
        { id: '2', title: 'Technical Core', status: 'in-progress', description: 'Data Structures, OS, DBMS and System Design principles.' },
        { id: '3', title: 'Company Coding', status: 'upcoming', description: 'Advanced DSA patterns found in previous interview sets.' },
        { id: '4', title: 'Mock Simulation', status: 'upcoming', description: 'Behavioral rounds and technical discussion practice.' }
    ];

    const displayStages = stages.length > 0 ? stages : defaultStages;

    return (
        <div className="roadmap-tree-container">
            <div className="roadmap-path-line"></div>
            <div className="roadmap-stages">
                {displayStages.map((stage, index) => {
                    const isCompleted = stage.status === 'completed' || stage.score >= 80;
                    const isInProgress = stage.status === 'in-progress' || (stage.score > 0 && stage.score < 80);
                    const isLocked = !isCompleted && !isInProgress;

                    return (
                        <div 
                            key={stage.id || index} 
                            className={`roadmap-node-wrapper ${stage.status} ${isCompleted ? 'completed' : ''} ${isInProgress ? 'active' : ''}`}
                        >
                            <div className="roadmap-connector">
                                <div className="connector-dot"></div>
                            </div>
                            
                            <div className="roadmap-node-card glass-card">
                                <div className="node-icon-container">
                                    {isCompleted ? (
                                        <CheckCircle2 size={24} color="#10b981" />
                                    ) : isInProgress ? (
                                        <div className="pulse-ripple">
                                            <Target size={24} color="#6366f1" />
                                        </div>
                                    ) : (
                                        <Circle size={24} color="#94a3b8" />
                                    )}
                                </div>
                                
                                <div className="node-content">
                                    <div className="node-header">
                                        <h4>{stage.title || stage.name || `Phase ${index + 1}`}</h4>
                                        {stage.score !== undefined && (
                                            <span className="node-score">{Math.round(stage.score)}%</span>
                                        )}
                                    </div>
                                    <p>{stage.description || 'Focus on patterns and optimization techniques.'}</p>
                                    
                                    {isInProgress && (
                                        <div className="node-action" onClick={stage.onAction}>
                                            <span>Continue Journey</span>
                                            <ArrowRight size={16} />
                                        </div>
                                    )}
                                </div>

                                {isCompleted && (
                                    <div className="node-achievement">
                                        <Trophy size={16} />
                                        <span>Mastered</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default RoadmapTree;
