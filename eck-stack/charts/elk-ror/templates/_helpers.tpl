{{- define "chart.name" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "kibana.labels" -}}
helm.sh/chart: {{ include "chart.name" . }}
app.kubernetes.io/name: kibana-ror
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "elasticsearch.labels" -}}
helm.sh/chart: {{ include "chart.name" . }}
app.kubernetes.io/name: elasticsearch-ror
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}