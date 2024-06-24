{{- define "chart.name" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "filebeat.labels" -}}
helm.sh/chart: {{ include "chart.name" . }}
app.kubernetes.io/name: {{ .Values.filebeat.name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "metricbeat.labels" -}}
helm.sh/chart: {{ include "chart.name" . }}
app.kubernetes.io/name: {{ .Values.metricbeat.name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}