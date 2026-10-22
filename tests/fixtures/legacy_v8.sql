-- Frozen schema from the reviewed comprehensive v8 fixture; no records.
PRAGMA user_version=8;
CREATE TABLE Worker (
            id TEXT PRIMARY KEY,                      -- Worker ID (alphanumeric)
            first_name TEXT,                          -- First Name
            last_name TEXT,                           -- Last Name
            year_of_birth INTEGER,                   -- Year of Birth
            month_of_birth INTEGER,                  -- Month of Birth
            day_of_birth INTEGER,                    -- Day of Birth
            gender TEXT,                             -- Gender (Male/Female)
            height REAL,                             -- Height (cm)
            weight REAL,                             -- Weight (kg)
            address TEXT,                            -- Address
            email TEXT,                              -- Email
            year_of_hiring INTEGER,                  -- Year of Hiring
            month_of_hiring INTEGER,                 -- Month of Hiring
            day_of_hiring INTEGER,                   -- Day of Hiring
            city TEXT,                               -- City
            state TEXT,                              -- State
            country TEXT,                            -- Country
            zipcode TEXT,                            -- Zip Code
    
            -- Head and Neck Measurements (examples)
            head_circumference REAL,                 -- Head Circumference (cm)
            neck_circumference REAL,                 -- Neck Circumference (cm)
            head_length REAL,                        -- Head Length (cm)
            neck_angle REAL,                         -- Neck Angle (degrees)
            head_angle REAL,                         -- Head Angle (degrees)
    
            -- Upper Body Measurements (examples)
            shoulder_width REAL,                     -- Shoulder Width (cm)
            chest_circumference REAL,                -- Chest Circumference (cm)
            upper_arm_length REAL,                   -- Upper Arm Length (cm)
            forearm_length REAL,                     -- Forearm Length (cm)
            hand_length REAL,                        -- Hand Length (cm)
    
            -- Lower Body Measurements (examples)
            hip_width REAL,                          -- Hip Width (cm)
            leg_length REAL,                         -- Leg Length (cm)
            thigh_length REAL,                       -- Thigh Length (cm)
            foot_length REAL,                        -- Foot Length (cm)
            knee_angle REAL                          -- Knee Angle (degrees)
    
            -- TODO: Add additional measurements from Head and Neck, Upper Body, and Lower Body tabs
        );
CREATE TABLE Section (
            plant_name TEXT NOT NULL,                         -- Foreign key referencing Plant table
            name TEXT NOT NULL,                               -- Primary key for the Section table
            description TEXT,                                 -- Section description
            location TEXT,                                    -- Section location
            capacity REAL,                                    -- Section capacity
            area REAL,                                        -- Section area
            creation_date TEXT,                               -- Section creation date
    
            -- Visual elements
            x REAL,                                           -- X Coordinate
            y REAL,                                           -- Y Coordinate
            width REAL,                                       -- Width
            height REAL,                                      -- Height
            line_thickness REAL,                              -- Line Thickness
            scale_x REAL,                                     -- Scale X
            scale_y REAL,                                     -- Scale Y
            crop_x REAL,                                      -- Crop X
            crop_y REAL,                                      -- Crop Y
            crop_width REAL,                                  -- Crop Width
            crop_height REAL,                                 -- Crop Height
            zoom REAL,                                        -- Zoom Level
            rotation REAL,                                    -- Rotation
            mirror_h INTEGER,                                 -- Horizontal Mirror
            mirror_v INTEGER,                                 -- Vertical Mirror
            orientation TEXT,                                 -- Orientation (e.g., Horizontal, Vertical)
            color TEXT,                                       -- Color
            brightness REAL,                                  -- Brightness
            contrast REAL,                                    -- Contrast
            saturation REAL,                                  -- Saturation
            lock INTEGER,                                     -- Lock State (0 or 1)
            visible INTEGER,                                  -- Visibility (0 or 1)
            transparency REAL,                                -- Transparency (0.0–1.0)
            enable INTEGER,                                   -- Enable State (0 or 1)
        
            PRIMARY KEY (plant_name, name),                   -- Composite primary key (plant_name and section name)
            FOREIGN KEY (plant_name) REFERENCES Plant(name) ON DELETE CASCADE   -- Foreign key relationship with the Plant table
        );
CREATE TABLE Line (
            plant_name TEXT NOT NULL,                         -- Foreign key referencing Plant table
            section_name TEXT NOT NULL,                       -- Foreign key referencing Section table
            name TEXT NOT NULL,                               -- Primary key for the Line table
            description TEXT,                                 -- Line description
            location TEXT,                                    -- Line location
            products TEXT,                                    -- Products processed by the line
            creation_date TEXT,                               -- Line creation date
        
            -- Visual elements
            x REAL,                                           -- X Coordinate
            y REAL,                                           -- Y Coordinate
            width REAL,                                       -- Width
            height REAL,                                      -- Height
            line_thickness REAL,                              -- Line Thickness
            scale_x REAL,                                     -- Scale X
            scale_y REAL,                                     -- Scale Y
            crop_x REAL,                                      -- Crop X
            crop_y REAL,                                      -- Crop Y
            crop_width REAL,                                  -- Crop Width
            crop_height REAL,                                 -- Crop Height
            zoom REAL,                                        -- Zoom Level
            rotation REAL,                                    -- Rotation
            mirror_h INTEGER,                                 -- Horizontal Mirror
            mirror_v INTEGER,                                 -- Vertical Mirror
            orientation TEXT,                                 -- Orientation (e.g., Horizontal, Vertical)
            color TEXT,                                       -- Color
            brightness REAL,                                  -- Brightness
            contrast REAL,                                    -- Contrast
            saturation REAL,                                  -- Saturation
            lock INTEGER,                                     -- Lock State (0 or 1)
            visible INTEGER,                                  -- Visibility (0 or 1)
            transparency REAL,                                -- Transparency (0.0–1.0)
            enable INTEGER,                                   -- Enable State (0 or 1)
            
            -- PRIMARY KEY (plant_name, section_name, name),     -- Composite primary key (plant_name, section_name, line name)
            -- FOREIGN KEY (plant_name) REFERENCES Plant(name),  -- Foreign key relationship with the Plant table
            -- FOREIGN KEY (section_name) REFERENCES Section(name) -- Foreign key relationship with the Section table
            PRIMARY KEY (plant_name, section_name, name),     -- Composite primary key
            FOREIGN KEY (plant_name, section_name) REFERENCES Section (plant_name, name) ON DELETE CASCADE

        );
CREATE TABLE Station (
            plant_name TEXT NOT NULL,                         -- Foreign key referencing Plant table
            section_name TEXT NOT NULL,                       -- Foreign key referencing Section table
            line_name TEXT NOT NULL,                          -- Foreign key referencing Line table
            id TEXT NOT NULL,                                 -- Primary key for the Station table
            location TEXT,                                    -- Workstation location
            task_description TEXT,                            -- Description of tasks performed
            equipment_used TEXT,                              -- Equipment used at the workstation
            cycle_time REAL,                                  -- Cycle time (in seconds)
            capacity INTEGER,                                 -- Workstation capacity
            ergonomic_risk_level REAL,                        -- Ergonomic risk level (0-100)
            performance_metric TEXT,                          -- Performance metric (e.g., efficiency %)
            power_consumption REAL,                           -- Power consumption (kW)
            materials_used TEXT,                              -- Materials processed or used at the workstation
            creation_date TEXT,                               -- Workstation creation date
            
            -- Visual elements
            x REAL,                                           -- X Coordinate
            y REAL,                                           -- Y Coordinate
            width REAL,                                       -- Width
            height REAL,                                      -- Height
            line_thickness REAL,                              -- Line Thickness
            scale_x REAL,                                     -- Scale X
            scale_y REAL,                                     -- Scale Y
            crop_x REAL,                                      -- Crop X
            crop_y REAL,                                      -- Crop Y
            crop_width REAL,                                  -- Crop Width
            crop_height REAL,                                 -- Crop Height
            zoom REAL,                                        -- Zoom Level
            rotation REAL,                                    -- Rotation
            mirror_h INTEGER,                                 -- Horizontal Mirror
            mirror_v INTEGER,                                 -- Vertical Mirror
            orientation TEXT,                                 -- Orientation (e.g., Horizontal, Vertical)
            color TEXT,                                       -- Color
            brightness REAL,                                  -- Brightness
            contrast REAL,                                    -- Contrast
            saturation REAL,                                  -- Saturation
            lock INTEGER,                                     -- Lock State (0 or 1)
            visible INTEGER,                                  -- Visibility (0 or 1)
            transparency REAL,                                -- Transparency (0.0–1.0)
            enable INTEGER,                                   -- Enable State (0 or 1)
        
            PRIMARY KEY (plant_name, section_name, line_name, id),   -- Composite primary key
            FOREIGN KEY (plant_name, section_name, line_name) 
            REFERENCES Line (plant_name, section_name, name) ON DELETE CASCADE     -- Foreign key relationship with the Line table
        );
CREATE TABLE Shift (
            id TEXT NOT NULL PRIMARY KEY,         -- Primary key for the Shift table (independent)
            description TEXT,                     -- Shift description
            start_time TEXT,                      -- Shift start time (HH:MM format)
            end_time TEXT,                        -- Shift end time (HH:MM format)
            shift_type TEXT,                      -- Type of shift (e.g., Morning, Night)
            tasks_performed TEXT,                 -- List of tasks performed
            product_output REAL,                  -- Product output count
            downtime REAL,                         -- Downtime during the shift (in hours)
            incidents_reported TEXT,              -- List of reported incidents
            ergonomic_risk_events TEXT,           -- Ergonomic risk events reported
            notes TEXT                            -- Additional notes
        );
CREATE TABLE ErgoTool (
            id TEXT NOT NULL PRIMARY KEY,   -- Primary key for the ergonomic tool (text format)
            name TEXT NOT NULL,             -- Name of the ergonomic tool
            description TEXT,               -- Description of the tool's purpose
            authors TEXT                    -- Authors or contributors of the tool
        );
CREATE TABLE WorkerStationShiftErgoTool (
            worker_id TEXT NOT NULL,               -- Foreign key referencing Worker table
            plant_name TEXT NOT NULL,              -- Foreign key referencing Station table
            section_name TEXT NOT NULL,            -- Foreign key referencing Station table
            line_name TEXT NOT NULL,               -- Foreign key referencing Station table
            station_id TEXT NOT NULL,              -- Foreign key referencing Station table
            shift_id TEXT NOT NULL,                -- Foreign key referencing Shift table
            tool_id TEXT NOT NULL,                 -- Foreign key referencing ErgoTool table
    
            total_cumulative_damage REAL,          -- Cumulative damage percentage
            probability_outcome REAL,              -- Probability of outcome
    
            -- Additional result fields
            result_3 REAL,
            result_4 REAL,
            result_5 REAL,
            result_6 REAL,
            result_7 REAL,
            result_8 REAL,
            result_9 REAL,
            unit TEXT,                             -- Measurement unit (Metric/Imperial)
    
            -- Visual elements
            x REAL,                                -- X Coordinate
            y REAL,                                -- Y Coordinate
            width REAL,                            -- Width
            height REAL,                           -- Height
            line_thickness REAL,                   -- Line Thickness
            scale_x REAL,                          -- Scale X
            scale_y REAL,                          -- Scale Y
            crop_x REAL,                           -- Crop X
            crop_y REAL,                           -- Crop Y
            crop_width REAL,                       -- Crop Width
            crop_height REAL,                      -- Crop Height
            zoom REAL,                             -- Zoom Level
            rotation REAL,                         -- Rotation
            mirror_h INTEGER,                      -- Horizontal Mirror
            mirror_v INTEGER,                      -- Vertical Mirror
            orientation TEXT,                      -- Orientation (e.g., Horizontal, Vertical)
            color TEXT,                            -- Color
            r INTEGER,                             -- Red value (0-255)
            g INTEGER,                             -- Green value (0-255)
            b INTEGER,                             -- Blue value (0-255)
            brightness REAL,                        -- Brightness
            contrast REAL,                          -- Contrast
            saturation REAL,                        -- Saturation
            lock INTEGER,                           -- Lock State (0 or 1)
            visible INTEGER,                        -- Visibility (0 or 1)
            transparency REAL,                      -- Transparency (0.0–1.0)
            enable INTEGER,                         -- Enable State (0 or 1)
    
            PRIMARY KEY (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id),  
            FOREIGN KEY (worker_id) REFERENCES Worker (id) ON DELETE CASCADE,
            FOREIGN KEY (plant_name, section_name, line_name, station_id) REFERENCES Station (plant_name, section_name, line_name, id) ON DELETE CASCADE,
            FOREIGN KEY (shift_id) REFERENCES Shift (id) ON DELETE CASCADE,
            FOREIGN KEY (tool_id) REFERENCES ErgoTool (id) ON DELETE CASCADE
        );
CREATE TABLE LifftResults (
            worker_id TEXT NOT NULL,              -- Foreign key referencing WorkerStationShiftErgoTool
            plant_name TEXT NOT NULL,             -- Foreign key referencing WorkerStationShiftErgoTool
            section_name TEXT NOT NULL,           -- Foreign key referencing WorkerStationShiftErgoTool
            line_name TEXT NOT NULL,              -- Foreign key referencing WorkerStationShiftErgoTool
            station_id TEXT NOT NULL,             -- Foreign key referencing WorkerStationShiftErgoTool
            shift_id TEXT NOT NULL,               -- Foreign key referencing WorkerStationShiftErgoTool
            tool_id TEXT NOT NULL,                -- Foreign key referencing WorkerStationShiftErgoTool
            task_id INTEGER NOT NULL,             -- Task identifier
    
            lever_arm REAL,                       -- Lever arm measurement
            load REAL,                            -- Load value
            moment REAL,                          -- Moment calculation
            repetitions INTEGER,                  -- Number of repetitions
            cumulative_damage REAL,               -- Cumulative damage percentage
            percentage_total REAL,                -- Total percentage of risk
    
            PRIMARY KEY (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id, task_id),  
            FOREIGN KEY (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id) 
            REFERENCES WorkerStationShiftErgoTool (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id) ON DELETE CASCADE
        );
CREATE TABLE DuetResults (
            worker_id TEXT NOT NULL,              -- Foreign key referencing WorkerStationShiftErgoTool
            plant_name TEXT NOT NULL,             -- Foreign key referencing WorkerStationShiftErgoTool
            section_name TEXT NOT NULL,           -- Foreign key referencing WorkerStationShiftErgoTool
            line_name TEXT NOT NULL,              -- Foreign key referencing WorkerStationShiftErgoTool
            station_id TEXT NOT NULL,             -- Foreign key referencing WorkerStationShiftErgoTool
            shift_id TEXT NOT NULL,               -- Foreign key referencing WorkerStationShiftErgoTool
            tool_id TEXT NOT NULL,                -- Foreign key referencing WorkerStationShiftErgoTool
            task_id INTEGER NOT NULL,             -- Task identifier
        
            omni_res_scale INTEGER,               -- Omni resistance scale
            repetitions INTEGER,                  -- Number of repetitions
            cumulative_damage REAL,               -- Cumulative damage percentage
            percentage_total REAL,                -- Total percentage of risk
        
            PRIMARY KEY (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id, task_id),  
            FOREIGN KEY (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id) 
            REFERENCES WorkerStationShiftErgoTool (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id) ON DELETE CASCADE
        );
CREATE TABLE TstResults (
            worker_id TEXT NOT NULL,              -- Foreign key referencing WorkerStationShiftErgoTool
            plant_name TEXT NOT NULL,             -- Foreign key referencing WorkerStationShiftErgoTool
            section_name TEXT NOT NULL,           -- Foreign key referencing WorkerStationShiftErgoTool
            line_name TEXT NOT NULL,              -- Foreign key referencing WorkerStationShiftErgoTool
            station_id TEXT NOT NULL,             -- Foreign key referencing WorkerStationShiftErgoTool
            shift_id TEXT NOT NULL,               -- Foreign key referencing WorkerStationShiftErgoTool
            tool_id TEXT NOT NULL,                -- Foreign key referencing WorkerStationShiftErgoTool
            task_id INTEGER NOT NULL,             -- Task identifier
        
            type_of_task INTEGER,                 -- Type of task
            lever_arm REAL,                       -- Lever arm measurement
            load REAL,                            -- Load value
            moment REAL,                          -- Moment calculation
            repetitions INTEGER,                  -- Number of repetitions
            cumulative_damage REAL,               -- Cumulative damage percentage
            percentage_total REAL,                -- Total percentage of risk
      
            PRIMARY KEY (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id, task_id),  
            FOREIGN KEY (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id) 
            REFERENCES WorkerStationShiftErgoTool (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id) ON DELETE CASCADE
        );
CREATE TABLE JobMeasurement (
                job_id TEXT NOT NULL,
                tool_id TEXT NOT NULL,
                total_cumulative_damage REAL,
                probability_outcome REAL,
                color TEXT,
                PRIMARY KEY (job_id, tool_id),
                FOREIGN KEY (job_id) REFERENCES Job (id) ON DELETE CASCADE,
                FOREIGN KEY (tool_id) REFERENCES ErgoTool (id) ON DELETE CASCADE
            );
CREATE TABLE SchemaMigration (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            application_version TEXT
        );
CREATE TABLE "Plant" (
            name TEXT PRIMARY KEY,
            description TEXT,
            location TEXT,
            type TEXT,
            area REAL,
            number_of_shifts INTEGER,
            start_time TEXT,
            end_time TEXT,
            operational_hours REAL,
            production_capacity REAL,
            opening_date TEXT,
            years_of_operation INTEGER,
            image_name TEXT,
            image_path TEXT,
            x REAL,
            y REAL,
            width REAL,
            height REAL,
            scale_x REAL,
            scale_y REAL,
            crop_x REAL,
            crop_y REAL,
            crop_width REAL,
            crop_height REAL,
            zoom REAL,
            rotation REAL,
            mirror_h INTEGER,
            mirror_v INTEGER,
            orientation TEXT,
            color TEXT,
            brightness REAL,
            contrast REAL,
            saturation REAL,
            lock INTEGER,
            visible INTEGER,
            transparency REAL,
            enable INTEGER
        );
CREATE TABLE "Job" (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
CREATE TABLE JobRiskMeasurement (
            profile_id INTEGER NOT NULL,
            tool_id TEXT NOT NULL,
            total_cumulative_damage REAL CHECK (
                total_cumulative_damage IS NULL OR total_cumulative_damage >= 0
            ),
            probability_outcome REAL CHECK (
                probability_outcome IS NULL OR probability_outcome BETWEEN 0 AND 100
            ),
            unit TEXT,
            notes TEXT,
            PRIMARY KEY (profile_id, tool_id),
            FOREIGN KEY (profile_id) REFERENCES JobRiskProfile (id) ON DELETE CASCADE,
            FOREIGN KEY (tool_id) REFERENCES ErgoTool (id) ON DELETE CASCADE
        );
CREATE TABLE WorkplaceContext (
            id INTEGER PRIMARY KEY,
            plant_name TEXT NOT NULL,
            section_name TEXT NOT NULL,
            line_name TEXT NOT NULL,
            station_id TEXT NOT NULL,
            shift_id TEXT NOT NULL,
            UNIQUE (plant_name, section_name, line_name, station_id, shift_id),
            FOREIGN KEY (plant_name, section_name, line_name, station_id)
                REFERENCES Station (plant_name, section_name, line_name, id)
                ON DELETE CASCADE,
            FOREIGN KEY (shift_id) REFERENCES Shift (id) ON DELETE CASCADE
        );
CREATE TABLE WorkerAssignment (
            id INTEGER PRIMARY KEY,
            worker_id TEXT NOT NULL,
            workplace_context_id INTEGER NOT NULL,
            job_placement_id INTEGER,
            started_at TEXT,
            ended_at TEXT,
            active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
            notes TEXT,
            CHECK (started_at IS NULL OR ended_at IS NULL OR started_at <= ended_at),
            FOREIGN KEY (worker_id) REFERENCES Worker (id) ON DELETE CASCADE,
            FOREIGN KEY (workplace_context_id) REFERENCES WorkplaceContext (id)
                ON DELETE CASCADE,
            FOREIGN KEY (job_placement_id) REFERENCES JobPlacement (id)
                ON DELETE SET NULL
        );
CREATE TABLE IndividualAssessment (
            id INTEGER PRIMARY KEY,
            worker_assignment_id INTEGER NOT NULL,
            tool_id TEXT NOT NULL,
            version INTEGER NOT NULL CHECK (version > 0),
            status TEXT NOT NULL CHECK (status IN ('draft', 'complete', 'superseded')),
            is_current INTEGER NOT NULL DEFAULT 0 CHECK (is_current IN (0, 1)),
            assessed_at TEXT,
            unit TEXT,
            total_cumulative_damage REAL CHECK (
                total_cumulative_damage IS NULL OR total_cumulative_damage >= 0
            ),
            probability_outcome REAL CHECK (
                probability_outcome IS NULL OR probability_outcome BETWEEN 0 AND 100
            ),
            notes TEXT,
            UNIQUE (worker_assignment_id, tool_id, version),
            FOREIGN KEY (worker_assignment_id) REFERENCES WorkerAssignment (id)
                ON DELETE CASCADE,
            FOREIGN KEY (tool_id) REFERENCES ErgoTool (id) ON DELETE CASCADE
        );
CREATE TABLE LiFFTAssessmentTask (
                individual_assessment_id INTEGER NOT NULL,
                task_index INTEGER NOT NULL CHECK (task_index >= 0),
                
            lever_arm REAL CHECK (lever_arm IS NULL OR lever_arm >= 0),
            load REAL CHECK (load IS NULL OR load >= 0),
            moment REAL CHECK (moment IS NULL OR moment >= 0),
            repetitions INTEGER CHECK (repetitions IS NULL OR repetitions >= 0),
            cumulative_damage REAL CHECK (cumulative_damage IS NULL OR cumulative_damage >= 0),
            percentage_total REAL CHECK (percentage_total IS NULL OR percentage_total >= 0)
        ,
                PRIMARY KEY (individual_assessment_id, task_index),
                FOREIGN KEY (individual_assessment_id) REFERENCES IndividualAssessment (id)
                    ON DELETE CASCADE
            );
CREATE TABLE DUETAssessmentTask (
                individual_assessment_id INTEGER NOT NULL,
                task_index INTEGER NOT NULL CHECK (task_index >= 0),
                
            omni_res_scale INTEGER CHECK (omni_res_scale IS NULL OR omni_res_scale BETWEEN 0 AND 10),
            repetitions INTEGER CHECK (repetitions IS NULL OR repetitions >= 0),
            cumulative_damage REAL CHECK (cumulative_damage IS NULL OR cumulative_damage >= 0),
            percentage_total REAL CHECK (percentage_total IS NULL OR percentage_total >= 0)
        ,
                PRIMARY KEY (individual_assessment_id, task_index),
                FOREIGN KEY (individual_assessment_id) REFERENCES IndividualAssessment (id)
                    ON DELETE CASCADE
            );
CREATE TABLE ShoulderAssessmentTask (
                individual_assessment_id INTEGER NOT NULL,
                task_index INTEGER NOT NULL CHECK (task_index >= 0),
                
            type_of_task INTEGER,
            lever_arm REAL CHECK (lever_arm IS NULL OR lever_arm >= 0),
            load REAL CHECK (load IS NULL OR load >= 0),
            moment REAL CHECK (moment IS NULL OR moment >= 0),
            repetitions INTEGER CHECK (repetitions IS NULL OR repetitions >= 0),
            cumulative_damage REAL CHECK (cumulative_damage IS NULL OR cumulative_damage >= 0),
            percentage_total REAL CHECK (percentage_total IS NULL OR percentage_total >= 0)
        ,
                PRIMARY KEY (individual_assessment_id, task_index),
                FOREIGN KEY (individual_assessment_id) REFERENCES IndividualAssessment (id)
                    ON DELETE CASCADE
            );
CREATE TABLE PlotAssessmentMarker (
            individual_assessment_id INTEGER PRIMARY KEY,
            x REAL,
            y REAL,
            width REAL,
            height REAL,
            line_thickness REAL,
            scale_x REAL,
            scale_y REAL,
            crop_x REAL,
            crop_y REAL,
            crop_width REAL,
            crop_height REAL,
            zoom REAL,
            rotation REAL,
            mirror_h INTEGER CHECK (mirror_h IS NULL OR mirror_h IN (0, 1)),
            mirror_v INTEGER CHECK (mirror_v IS NULL OR mirror_v IN (0, 1)),
            orientation TEXT,
            r INTEGER CHECK (r IS NULL OR r BETWEEN 0 AND 255),
            g INTEGER CHECK (g IS NULL OR g BETWEEN 0 AND 255),
            b INTEGER CHECK (b IS NULL OR b BETWEEN 0 AND 255),
            brightness REAL,
            contrast REAL,
            saturation REAL,
            lock INTEGER CHECK (lock IS NULL OR lock IN (0, 1)),
            visible INTEGER CHECK (visible IS NULL OR visible IN (0, 1)),
            transparency REAL CHECK (
                transparency IS NULL OR transparency BETWEEN 0 AND 1
            ),
            enable INTEGER CHECK (enable IS NULL OR enable IN (0, 1)),
            FOREIGN KEY (individual_assessment_id) REFERENCES IndividualAssessment (id)
                ON DELETE CASCADE
        );
CREATE TABLE "JobRiskProfile" (
            id INTEGER PRIMARY KEY,
            job_id TEXT NOT NULL,
            name TEXT NOT NULL,
            version INTEGER NOT NULL CHECK (version > 0),
            status TEXT NOT NULL CHECK (status IN ('draft', 'approved', 'retired')),
            is_current INTEGER NOT NULL DEFAULT 0 CHECK (is_current IN (0, 1)),
            source_type TEXT NOT NULL CHECK (
                source_type IN ('expert', 'external', 'study', 'aggregate', 'imported')
            ),
            source_reference TEXT,
            methodology TEXT,
            sample_size INTEGER CHECK (sample_size IS NULL OR sample_size >= 0),
            assessed_on TEXT,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (job_id, version),
            FOREIGN KEY (job_id) REFERENCES Job (id) ON DELETE CASCADE
        );
CREATE TABLE "JobPlacement" (
            id INTEGER PRIMARY KEY,
            job_id TEXT NOT NULL,
            workplace_context_id INTEGER NOT NULL,
            active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
            notes TEXT,
            FOREIGN KEY (job_id) REFERENCES Job (id) ON DELETE CASCADE,
            FOREIGN KEY (workplace_context_id) REFERENCES WorkplaceContext (id)
                ON DELETE CASCADE
        );
CREATE TABLE PlotStationPosition (
            plant_name TEXT NOT NULL,
            section_name TEXT NOT NULL,
            line_name TEXT NOT NULL,
            station_id TEXT NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL,
            position_source TEXT NOT NULL CHECK (
                position_source IN ('manual', 'worker', 'job', 'migration')
            ),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (plant_name, section_name, line_name, station_id),
            FOREIGN KEY (plant_name, section_name, line_name, station_id)
                REFERENCES Station (plant_name, section_name, line_name, id)
                ON DELETE CASCADE
        );
CREATE TABLE PlotWorkerAssignmentMarker (
            worker_assignment_id INTEGER PRIMARY KEY,
            x REAL,
            y REAL,
            size REAL NOT NULL DEFAULT 50 CHECK (size > 0),
            scale REAL NOT NULL DEFAULT 1 CHECK (scale > 0),
            line_thickness REAL NOT NULL DEFAULT 1 CHECK (line_thickness >= 0),
            locked INTEGER NOT NULL DEFAULT 0 CHECK (locked IN (0, 1)),
            visible INTEGER NOT NULL DEFAULT 0 CHECK (visible IN (0, 1)),
            enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
            position_source TEXT NOT NULL DEFAULT 'unplaced' CHECK (
                position_source IN ('unplaced', 'station_anchor', 'manual', 'migration')
            ),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK ((x IS NULL) = (y IS NULL)),
            CHECK (
                (position_source = 'unplaced' AND x IS NULL AND y IS NULL)
                OR
                (position_source != 'unplaced' AND x IS NOT NULL AND y IS NOT NULL)
            ),
            FOREIGN KEY (worker_assignment_id) REFERENCES WorkerAssignment (id)
                ON DELETE CASCADE
        );
CREATE TABLE RotationScheme (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            num_workers INTEGER NOT NULL CHECK (num_workers > 0),
            num_timeblocks INTEGER NOT NULL CHECK (num_timeblocks > 0),
            optimization_mode TEXT NOT NULL DEFAULT 'manual' CHECK (
                optimization_mode IN ('manual', 'single_tool', 'all_tools')
            ),
            primary_tool_id TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (primary_tool_id) REFERENCES ErgoTool (id) ON DELETE SET NULL
        );
CREATE TABLE RotationSchemeScope (
            scheme_id TEXT NOT NULL,
            workplace_context_id INTEGER NOT NULL,
            PRIMARY KEY (scheme_id, workplace_context_id),
            FOREIGN KEY (scheme_id) REFERENCES RotationScheme (id) ON DELETE CASCADE,
            FOREIGN KEY (workplace_context_id) REFERENCES WorkplaceContext (id)
                ON DELETE RESTRICT
        );
CREATE TABLE RotationTarget (
            id INTEGER PRIMARY KEY,
            scheme_id TEXT NOT NULL,
            job_id TEXT NOT NULL,
            job_placement_id INTEGER,
            job_risk_profile_id INTEGER NOT NULL,
            FOREIGN KEY (scheme_id) REFERENCES RotationScheme (id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES Job (id) ON DELETE RESTRICT,
            FOREIGN KEY (job_placement_id) REFERENCES JobPlacement (id) ON DELETE RESTRICT,
            FOREIGN KEY (job_risk_profile_id) REFERENCES JobRiskProfile (id)
                ON DELETE RESTRICT
        );
CREATE TABLE RotationAssignment (
            scheme_id TEXT NOT NULL,
            block_index INTEGER NOT NULL CHECK (block_index >= 0),
            worker_id TEXT NOT NULL,
            worker_assignment_id INTEGER,
            rotation_target_id INTEGER NOT NULL,
            PRIMARY KEY (scheme_id, block_index, worker_id),
            FOREIGN KEY (scheme_id) REFERENCES RotationScheme (id) ON DELETE CASCADE,
            FOREIGN KEY (worker_id) REFERENCES Worker (id) ON DELETE RESTRICT,
            FOREIGN KEY (worker_assignment_id) REFERENCES WorkerAssignment (id)
                ON DELETE RESTRICT,
            FOREIGN KEY (rotation_target_id) REFERENCES RotationTarget (id)
                ON DELETE RESTRICT
        );