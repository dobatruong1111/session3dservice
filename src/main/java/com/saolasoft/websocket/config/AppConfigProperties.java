package com.saolasoft.websocket.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import com.saolasoft.websocket.config.model.ViewerProperty;

@Configuration
@ConfigurationProperties(prefix="apps")
@Getter
@Setter
public class AppConfigProperties {
	
	private ViewerProperty viewer;
}
