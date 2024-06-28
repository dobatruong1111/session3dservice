package com.saolasoft.websocket.config.model;

import lombok.Getter;
import lombok.Setter;
import java.util.List;

@Getter
@Setter
public class ViewerProperty {

	private List<String> cmd;

	private String readyLine;
}
