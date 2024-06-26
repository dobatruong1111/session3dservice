package com.saolasoft.websocket.session3d.service;

import com.saolasoft.websocket.config.AppConfigProperties;
import com.saolasoft.websocket.config.ConfigProperties;
import com.saolasoft.websocket.session3d.model.Session3d;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.Duration;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class ProcessManager {

    private final Logger logger = LoggerFactory.getLogger(getClass());

    private ConfigProperties configProperties;

    private AppConfigProperties appConfigProperties;

    private final Map<String, Process> processes;

    public ProcessManager(ConfigProperties configProperties,
                          AppConfigProperties appConfigProperties) {
        this.configProperties = configProperties;
        this.appConfigProperties = appConfigProperties;
        this.processes = new HashMap<>();
    }

    public String getLogFilePath(String id) {
        return String.format("%s%s%s.txt", this.configProperties.getLogPath(), "/", id);
    }

    public boolean startProcess(Session3d session3d) {
        // Create log file
        String logFilePath = this.getLogFilePath(session3d.getId());

        try {
            // Set command to run
            ProcessBuilder builder = new ProcessBuilder(session3d.getCmd().split(" "));

            // Write to log file
            File logFile = new File(logFilePath);
            if (!logFile.exists()) {
                logFile.createNewFile();
            }
            builder.redirectOutput(ProcessBuilder.Redirect.appendTo(logFile));
            builder.redirectError(ProcessBuilder.Redirect.appendTo(logFile));

            // Start process
            Process process = builder.start();

            // Save process
            processes.put(session3d.getId(), process);

            // Check process is ready
            LocalTime startTime = LocalTime.now();
            int count = 0;
            while (true) {
                if (isReady(session3d, count)) {
                    return true;
                }

                Duration elapsedTime = Duration.between(startTime, LocalTime.now());
                if (elapsedTime.getSeconds() > this.configProperties.getTimeout()) {
                    stopProcess(session3d.getId());
                    return false;
                }

                try {
                    // Sleep 1 second
                    Thread.sleep(1000);
                } catch (Exception e) {
                    logger.info(e.getMessage());
                }
                count += 1;
            }
        } catch (Exception e) {
            logger.error(e.getMessage());
            return false;
        }
    }

    public void stopProcess(String id) {
        Process process = this.processes.get(id);
        try {
            process.destroy();
        } catch (Exception e) {
            logger.error(e.getMessage());
        }
    }

    public boolean isRunning(String id) {
        return this.processes.get(id).isAlive();
    }

    public List<String> listEndedProcess() {
        List<String> sessionToRelease = new ArrayList<>();
        for (String id : this.processes.keySet()) {
            if (!this.processes.get(id).isAlive()) {
                sessionToRelease.add(id);
            }
        }
        return sessionToRelease;
    }

    public boolean isReady(Session3d session3d, int count) {
        // The process has to be running to be ready
        if (!this.isRunning(session3d.getId()) && count < 60) {
            return false;
        }

        // Give up after 60 seconds if still not running
        if (!this.isRunning(session3d.getId())) {
            return true;
        }

        // Check the output for ready line
        String readyLine = this.appConfigProperties.getViewer().getReadyLine();
        boolean ready = false;
        try {
            String logFilePath = this.getLogFilePath(session3d.getId());
            String content = Files.readString(Paths.get(logFilePath));
            if (content.contains(readyLine)) {
                ready = true;
            }
        } catch (Exception e) {
            logger.error(e.getMessage());
        }
        return ready;
    }
}
