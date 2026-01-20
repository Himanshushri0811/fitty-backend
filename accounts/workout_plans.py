
DEFAULT_WORKOUT_PLANS = {
    "Weight Loss": [
        {
            "day_name": "Monday",
            "focus": "Full Body + Cardio",
            "exercises": [
                {"name": "Burpees", "sets": "4", "reps": "15", "description": "Full body explosive movement", "video_url": ""},
                {"name": "Jumping Jacks", "sets": "4", "reps": "45s", "description": "Cardio warm-up and endurance", "video_url": ""},
                {"name": "Squat Jumps", "sets": "3", "reps": "15", "description": "Explosive leg power", "video_url": ""},
                {"name": "Push-ups", "sets": "3", "reps": "12", "description": "Upper body strength", "video_url": ""},
                {"name": "Mountain Climbers", "sets": "3", "reps": "30s", "description": "Core and cardio burner", "video_url": ""}
            ]
        },
        {
            "day_name": "Tuesday",
            "focus": "Upper Body + HIIT",
            "exercises": [
                {"name": "Dumbbell Press", "sets": "3", "reps": "12", "description": "Chest and triceps", "video_url": ""},
                {"name": "Bent Over Rows", "sets": "3", "reps": "12", "description": "Back strengthening", "video_url": ""},
                {"name": "Shoulder Taps", "sets": "3", "reps": "20", "description": "Core stability and shoulders", "video_url": ""},
                {"name": "High Knees", "sets": "4", "reps": "30s", "description": "High intensity cardio", "video_url": ""}
            ]
        },
        {
            "day_name": "Wednesday",
            "focus": "Lower Body + Core",
            "exercises": [
                {"name": "Walking Lunges", "sets": "3", "reps": "20", "description": "Leg endurance", "video_url": ""},
                {"name": "Glute Bridges", "sets": "3", "reps": "15", "description": "Posterior chain", "video_url": ""},
                {"name": "Plank", "sets": "3", "reps": "45s", "description": "Static core hold", "video_url": ""},
                {"name": "Leg Raises", "sets": "3", "reps": "15", "description": "Lower abs focus", "video_url": ""}
            ]
        },
        {
            "day_name": "Thursday",
            "focus": "Cardio + Endurance",
            "exercises": [
                {"name": "Running / Jogging", "sets": "1", "reps": "30m", "description": "Steady state cardio", "video_url": ""},
                {"name": "Cycling", "sets": "1", "reps": "20m", "description": "Low impact endurance", "video_url": ""}
            ]
        },
        {
            "day_name": "Friday",
            "focus": "Full Body (Light Weights)",
            "exercises": [
                {"name": "Thrusters", "sets": "3", "reps": "12", "description": "Squat to overhead press", "video_url": ""},
                {"name": "Renegade Rows", "sets": "3", "reps": "10/side", "description": "Core and back stability", "video_url": ""},
                {"name": "Step Ups", "sets": "3", "reps": "12/leg", "description": "Unilateral leg strength", "video_url": ""}
            ]
        },
        {
            "day_name": "Saturday",
            "focus": "Mobility + Stretching",
            "exercises": [
                {"name": "Dynamic Stretching", "sets": "1", "reps": "15m", "description": "Full body flow", "video_url": ""},
                {"name": "Foam Rolling", "sets": "1", "reps": "10m", "description": "Myofascial release", "video_url": ""}
            ]
        },
        {
            "day_name": "Sunday",
            "focus": "Rest",
            "exercises": []
        }
    ],
    "Muscle Building": [
        {
            "day_name": "Monday",
            "focus": "Chest + Triceps",
            "exercises": [
                {"name": "Bench Press", "sets": "4", "reps": "8-12", "description": "Focus: Chest size, push strength", "video_url": ""},
                {"name": "Incline Dumbbell Press", "sets": "3", "reps": "10", "description": "Upper chest focus", "video_url": ""},
                {"name": "Chest Fly", "sets": "3", "reps": "12", "description": "Chest isolation", "video_url": ""},
                {"name": "Tricep Dips", "sets": "3", "reps": "12", "description": "Tricep mass builder", "video_url": ""},
                {"name": "Cable Pushdown", "sets": "3", "reps": "15", "description": "Tricep definition", "video_url": ""}
            ]
        },
        {
            "day_name": "Tuesday",
            "focus": "Back + Biceps",
            "exercises": [
                {"name": "Deadlift", "sets": "4", "reps": "6-8", "description": "Total back and posterior chain", "video_url": ""},
                {"name": "Pull Ups", "sets": "3", "reps": "AMRAP", "description": "Lat width", "video_url": ""},
                {"name": "Barbell Rows", "sets": "3", "reps": "10", "description": "Back thickness", "video_url": ""},
                {"name": "Barbell Curls", "sets": "3", "reps": "12", "description": "Bicep mass", "video_url": ""},
                {"name": "Hammer Curls", "sets": "3", "reps": "12", "description": "Forearm and brachialis", "video_url": ""}
            ]
        },
        {
            "day_name": "Wednesday",
            "focus": "Legs + Core",
            "exercises": [
                {"name": "Squats", "sets": "4", "reps": "8-10", "description": "Leg builder", "video_url": ""},
                {"name": "Leg Press", "sets": "3", "reps": "12", "description": "Quad focus", "video_url": ""},
                {"name": "Romanian Deadlift", "sets": "3", "reps": "10", "description": "Hamstring focus", "video_url": ""},
                {"name": "Calf Raises", "sets": "4", "reps": "15", "description": "Calves isolation", "video_url": ""},
                {"name": "Plank", "sets": "3", "reps": "60s", "description": "Core stability", "video_url": ""}
            ]
        },
        {
            "day_name": "Thursday",
            "focus": "Rest / Light Cardio",
            "exercises": [
                {"name": "Walking", "sets": "1", "reps": "30m", "description": "Active recovery", "video_url": ""}
            ]
        },
        {
            "day_name": "Friday",
            "focus": "Shoulders + Arms",
            "exercises": [
                {"name": "Overhead Press", "sets": "4", "reps": "8-10", "description": "Shoulder mass", "video_url": ""},
                {"name": "Lateral Raises", "sets": "4", "reps": "15", "description": "Side delts", "video_url": ""},
                {"name": "Face Pulls", "sets": "3", "reps": "15", "description": "Rear delts and posture", "video_url": ""},
                {"name": "Bicep Curls", "sets": "3", "reps": "12", "description": "Arm pump", "video_url": ""},
                {"name": "Tricep Extensions", "sets": "3", "reps": "12", "description": "Arm definition", "video_url": ""}
            ]
        },
        {
            "day_name": "Saturday",
            "focus": "Weak Muscles / Abs",
            "exercises": [
                {"name": "Cable Crunches", "sets": "3", "reps": "15", "description": "Weighted ab work", "video_url": ""},
                {"name": "Hanging Leg Raises", "sets": "3", "reps": "12", "description": "Lower abs", "video_url": ""},
                {"name": "Focus Area Exercise", "sets": "3", "reps": "12", "description": "Target lagging body part", "video_url": ""}
            ]
        },
        {
            "day_name": "Sunday",
            "focus": "Rest",
            "exercises": []
        }
    ],
    "Endurance Building": [
        {
            "day_name": "Monday",
            "focus": "Cardio (Steady State)",
            "exercises": [{"name": "Long Run", "sets": "1", "reps": "45m", "description": "Zone 2 Training", "video_url": ""}]
        },
        {
            "day_name": "Tuesday",
            "focus": "Upper Body + Endurance",
            "exercises": [
                {"name": "Circuit Training", "sets": "3", "reps": "15 reps/station", "description": "Pushups, Rows, Press with minimal rest", "video_url": ""},
                {"name": "Battle Ropes", "sets": "4", "reps": "30s", "description": "Conditioning", "video_url": ""}
            ]
        },
        {
            "day_name": "Wednesday",
            "focus": "Cardio + Core",
            "exercises": [
                {"name": "Interval Running", "sets": "1", "reps": "20m", "description": "1m hard, 1m easy", "video_url": ""},
                {"name": "Plank Circuit", "sets": "3", "reps": "3m total", "description": "Front and side planks", "video_url": ""}
            ]
        },
        {
            "day_name": "Thursday",
            "focus": "Lower Body + Endurance",
            "exercises": [
                {"name": "Box Jumps", "sets": "3", "reps": "15", "description": "Plyometrics", "video_url": ""},
                {"name": "Jump Lunges", "sets": "3", "reps": "20", "description": "Leg stamina", "video_url": ""}
            ]
        },
        {
            "day_name": "Friday",
            "focus": "Long Duration Cardio",
            "exercises": [{"name": "Cycling / Rowing", "sets": "1", "reps": "60m", "description": "Aerobic base building", "video_url": ""}]
        },
        {
            "day_name": "Saturday",
            "focus": "Mobility + Recovery",
            "exercises": [{"name": "Yoga Flow", "sets": "1", "reps": "30m", "description": "Restore range of motion", "video_url": ""}]
        },
        {
            "day_name": "Sunday",
            "focus": "Rest",
            "exercises": []
        }
    ],
    "Flexibility & Mobility": [
        {
            "day_name": "Monday",
            "focus": "Upper Body Mobility",
            "exercises": [{"name": "Shoulder Dislocations", "sets": "3", "reps": "15", "description": "Shoulder health", "video_url": ""}, {"name": "Thoracic Extension", "sets": "3", "reps": "10", "description": "Spine mobility", "video_url": ""}]
        },
        {
            "day_name": "Tuesday",
            "focus": "Lower Body Mobility",
            "exercises": [{"name": "90/90 Stretch", "sets": "2", "reps": "2m/side", "description": "Hip mobility", "video_url": ""}, {"name": "Deep Squat Hold", "sets": "3", "reps": "1m", "description": "Ankle and hip opener", "video_url": ""}]
        },
        {
            "day_name": "Wednesday",
            "focus": "Spine + Core Mobility",
            "exercises": [{"name": "Cat-Cow", "sets": "3", "reps": "10", "description": "Spinal flexion/extension", "video_url": ""}, {"name": "Bird Dog", "sets": "3", "reps": "10/side", "description": "Core stability", "video_url": ""}]
        },
        {
            "day_name": "Thursday",
            "focus": "Full Body Stretch",
            "exercises": [{"name": "Static Stretching Routine", "sets": "1", "reps": "30m", "description": "Hold each stretch 30s+", "video_url": ""}]
        },
        {
            "day_name": "Friday",
            "focus": "Balance + Stability",
            "exercises": [{"name": "Single Leg Balance", "sets": "3", "reps": "1m/leg", "description": "Proprioception", "video_url": ""}, {"name": "Bosu Ball Squats", "sets": "3", "reps": "15", "description": "Stability", "video_url": ""}]
        },
        {
            "day_name": "Saturday",
            "focus": "Yoga / Deep Stretch",
            "exercises": [{"name": "Vinyasa Flow", "sets": "1", "reps": "45m", "description": "Movement meditation", "video_url": ""}]
        },
        {
            "day_name": "Sunday",
            "focus": "Rest",
            "exercises": []
        }
    ],
    "Hybrid / All-Round Fitness": [
        {
            "day_name": "Monday",
            "focus": "Chest + Triceps",
            "exercises": [
                {"name": "Bench Press", "sets": "4", "reps": "8-12", "description": "Focus: Chest size, push strength", "video_url": ""},
                {"name": "Incline Dumbbell Press", "sets": "3", "reps": "10-12", "description": "Upper chest development", "video_url": ""},
                {"name": "Decline Press / Push-Ups", "sets": "3", "reps": "12", "description": "Lower chest", "video_url": ""},
                {"name": "Chest Fly (Machine / Dumbbell)", "sets": "3", "reps": "12-15", "description": "Chest isolation and stretch", "video_url": ""},
                {"name": "Cable Crossover", "sets": "3", "reps": "15", "description": "Inner chest definition", "video_url": ""},
                {"name": "Triceps Dips", "sets": "3", "reps": "10-12", "description": "Compound movement for triceps", "video_url": ""},
                {"name": "Close-Grip Bench Press", "sets": "3", "reps": "10", "description": "Tricep mass", "video_url": ""},
                {"name": "Cable Pushdown", "sets": "3", "reps": "12-15", "description": "Tricep isolation and lockout", "video_url": ""},
                {"name": "Overhead Dumbbell Extension", "sets": "3", "reps": "12", "description": "Long head of triceps", "video_url": ""},
                {"name": "Skull Crushers", "sets": "3", "reps": "12", "description": "Tricep power", "video_url": ""}
            ]
        },
        {
            "day_name": "Tuesday",
            "focus": "Back + Biceps",
            "exercises": [
                {"name": "Pull-Ups / Lat Pulldown", "sets": "4", "reps": "8-12", "description": "Focus: Width + thickness", "video_url": ""},
                {"name": "Barbell Row", "sets": "4", "reps": "8-10", "description": "Back thickness and power", "video_url": ""},
                {"name": "Seated Cable Row", "sets": "3", "reps": "12", "description": "Mid-back development", "video_url": ""},
                {"name": "T-Bar Row", "sets": "3", "reps": "10", "description": "Back density", "video_url": ""},
                {"name": "Face Pull", "sets": "3", "reps": "15", "description": "Posture and rear delts", "video_url": ""},
                {"name": "Barbell / EZ Bar Curl", "sets": "3", "reps": "10-12", "description": "Bicep mass builder", "video_url": ""},
                {"name": "Hammer Curl", "sets": "3", "reps": "12", "description": "Brachialis and forearm width", "video_url": ""},
                {"name": "Preacher Curl", "sets": "3", "reps": "12", "description": "Bicep isolation", "video_url": ""},
                {"name": "Concentration Curl", "sets": "3", "reps": "15", "description": "Peak focus", "video_url": ""},
                {"name": "Cable Curl", "sets": "3", "reps": "15", "description": "Constant tension", "video_url": ""}
            ]
        },
        {
            "day_name": "Wednesday",
            "focus": "Legs + Core",
            "exercises": [
                {"name": "Squats / Leg Press", "sets": "4", "reps": "8-12", "description": "Focus: Lower body power", "video_url": ""},
                {"name": "Romanian Deadlift", "sets": "3", "reps": "10-12", "description": "Hamstring and glute focus", "video_url": ""},
                {"name": "Walking Lunges", "sets": "3", "reps": "20 steps", "description": "Unilateral leg strength", "video_url": ""},
                {"name": "Standing / Seated Calf Raises", "sets": "4", "reps": "15-20", "description": "Calf development", "video_url": ""},
                {"name": "Hip Thrust (Optional)", "sets": "3", "reps": "12", "description": "Glute isolation", "video_url": ""},
                {"name": "Plank", "sets": "3", "reps": "60s", "description": "Core stability", "video_url": ""},
                {"name": "Russian Twists", "sets": "3", "reps": "20", "description": "Oblique work", "video_url": ""}
            ]
        },
        {
            "day_name": "Thursday",
            "focus": "Cardio + Endurance",
            "exercises": [
                {"name": "Treadmill Run", "sets": "1", "reps": "30m", "description": "Cardio Base", "video_url": ""},
                {"name": "Jump Rope", "sets": "5", "reps": "1m", "description": "Conditioning", "video_url": ""},
                {"name": "Cycling", "sets": "1", "reps": "20m", "description": "Low impact endurance", "video_url": ""}
            ]
        },
        {
            "day_name": "Friday",
            "focus": "Shoulders + Arms",
            "exercises": [
                {"name": "Shoulder Press (Barbell / Dumbbell)", "sets": "4", "reps": "10", "description": "Focus: Shoulder width + stability", "video_url": ""},
                {"name": "Lateral Raises", "sets": "4", "reps": "15", "description": "Side delt isolation", "video_url": ""},
                {"name": "Front Raises", "sets": "3", "reps": "12", "description": "Front delt", "video_url": ""},
                {"name": "Rear Delt Fly", "sets": "3", "reps": "15", "description": "Rear delt", "video_url": ""},
                {"name": "Upright Row (Light)", "sets": "3", "reps": "15", "description": "Traps and delts", "video_url": ""},
                {"name": "Bicep Curls", "sets": "3", "reps": "12", "description": "Extra arm work", "video_url": ""},
                {"name": "Tricep Pushdowns", "sets": "3", "reps": "12", "description": "Extra arm work", "video_url": ""}
            ]
        },
        {
            "day_name": "Saturday",
            "focus": "Mobility + Flexibility",
            "exercises": [
                {"name": "Yoga & Stretching Flow", "sets": "1", "reps": "20 mins", "description": "Mobility and recovery", "video_url": ""},
                {"name": "Surya Namaskar", "sets": "5", "reps": "Rounds", "description": "Full body flow", "video_url": ""},
                {"name": "Deep Breathing / Pranayama", "sets": "1", "reps": "10 mins", "description": "Mental recovery", "video_url": ""}
            ]
        },
        {
            "day_name": "Sunday",
            "focus": "Rest",
            "exercises": []
        }
    ],
    "Beginner Safe Split": [
        {
            "day_name": "Monday",
            "focus": "Full Body",
            "exercises": [{"name": "Bodyweight Squats", "sets": "3", "reps": "10", "description": "", "video_url": ""}, {"name": "Pushups (Knees)", "sets": "3", "reps": "8", "description": "", "video_url": ""}]
        },
        {
            "day_name": "Tuesday",
            "focus": "Cardio",
            "exercises": [{"name": "Brisk Walk", "sets": "1", "reps": "20m", "description": "", "video_url": ""}]
        },
        {
            "day_name": "Wednesday",
            "focus": "Full Body",
            "exercises": [{"name": "Lunges", "sets": "2", "reps": "10", "description": "", "video_url": ""}, {"name": "Dumbbell Press", "sets": "2", "reps": "10", "description": "", "video_url": ""}]
        },
        {
            "day_name": "Thursday",
            "focus": "Cardio",
            "exercises": [{"name": "Brisk Walk", "sets": "1", "reps": "20m", "description": "", "video_url": ""}]
        },
        {
            "day_name": "Friday",
            "focus": "Full Body",
            "exercises": [{"name": "Plank", "sets": "2", "reps": "20s", "description": "", "video_url": ""}, {"name": "Goblet Squat", "sets": "2", "reps": "10", "description": "", "video_url": ""}]
        },
        {
            "day_name": "Saturday",
            "focus": "Stretching",
            "exercises": [{"name": "Full Body Stretch", "sets": "1", "reps": "10m", "description": "", "video_url": ""}]
        },
        {
            "day_name": "Sunday",
            "focus": "Rest",
            "exercises": []
        }
    ]
}
