package com.saolasoft.websocket.config.model;

import lombok.Getter;
import lombok.Setter;
import java.util.List;

@Getter
@Setter
public class ResourceProperty {
	
	private String host;

	private List<Integer> portRange;
}
