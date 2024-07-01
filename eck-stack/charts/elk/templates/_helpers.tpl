{{- define "chart.name" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "logstash.labels" -}}
helm.sh/chart: {{ include "chart.name" . }}
app.kubernetes.io/name: {{ .Values.logstash.name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "kibana.labels" -}}
helm.sh/chart: {{ include "chart.name" . }}
app.kubernetes.io/name: {{ .Values.kibana.name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "elasticsearch.labels" -}}
helm.sh/chart: {{ include "chart.name" . }}
app.kubernetes.io/name: {{ .Values.elasticsearch.name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "apmServer.labels" -}}
helm.sh/chart: {{ include "chart.name" . }}
app.kubernetes.io/name: {{ .Values.apmServer.name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "apmServer.nginx.labels" -}}
helm.sh/chart: {{ include "chart.name" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{ include "apmServer.nginx.selectorLabels" . }}
{{- end }}

{{- define "apmServer.nginx.selectorLabels" -}}
app.kubernetes.io/name: {{ .Values.apmServer.nginx.name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}