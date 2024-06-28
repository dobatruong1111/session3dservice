package com.saolasoft.websocket.config;

import java.util.List;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import com.saolasoft.websocket.config.model.ResourceProperty;

@Configuration
@ConfigurationProperties(prefix="configuration")
@Getter
@Setter
public class ConfigProperties {
	
	private String logPath;

	private String websocketUrl;

	private int timeout;

	private List<ResourceProperty> resources;
}
