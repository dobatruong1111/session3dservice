package com.saolasoft.websocket.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import com.saolasoft.websocket.config.model.ViewerProperty;

@Configuration
@ConfigurationProperties(prefix="apps")
public class AppConfigProperties {
	
	private ViewerProperty viewer;
	
	public ViewerProperty getViewer() {
		return this.viewer;
	}
	
	public void setViewer(ViewerProperty viewer) {
		this.viewer = viewer;
	}
}
