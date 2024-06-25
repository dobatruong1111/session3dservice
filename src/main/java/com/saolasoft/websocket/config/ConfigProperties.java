package com.saolasoft.websocket.config;

import java.util.List;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import com.saolasoft.websocket.config.model.ResourceProperty;

@Configuration
@ConfigurationProperties(prefix="configuration")
public class ConfigProperties {
	
	private String logPath;
	private String sessionUrl;
	private int timeout;
	private List<ResourceProperty> resources;
	
	public String getLogPath() {
		return this.logPath;
	}
	
	public String getSessionUrl() {
		return this.sessionUrl;
	}
	
	public int getTimeout() {
		return this.timeout;
	}
	
	public List<ResourceProperty> getResources() {
		return this.resources;
	}
	
	public void setLogPath(String logPath) {
		this.logPath = logPath;
	}
	
	public void setSessionUrl(String sessionUrl) {
		this.sessionUrl = sessionUrl;
	}
	
	public void setTimeout(int timeout) {
		this.timeout = timeout;
	}
	
	public void setResources(List<ResourceProperty> resources) {
		this.resources = resources;
	}
}
