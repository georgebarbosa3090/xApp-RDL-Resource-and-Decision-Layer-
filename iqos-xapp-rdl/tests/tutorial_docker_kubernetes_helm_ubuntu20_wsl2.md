# Tutorial: Docker, Kubernetes e Helm no Ubuntu 20.04.6 LTS em WSL2

> **Ambiente validado neste tutorial:** Windows + WSL2 + Ubuntu 20.04.6
> LTS, `systemd`, Docker Engine, containerd, Kubernetes via kubeadm,
> Flannel CNI e Helm.
>
> Este documento consolida o procedimento realizado e os erros
> encontrados durante a instalação, com diagnóstico e solução.

## 1. Arquitetura final

``` text
Windows
└── WSL2
    └── Ubuntu 20.04.6 LTS
        ├── systemd
        ├── Docker Engine
        │   ├── Docker CLI
        │   ├── Docker Compose
        │   └── Buildx
        ├── containerd
        ├── Kubernetes
        │   ├── kubeadm
        │   ├── kubelet
        │   ├── kubectl
        │   ├── etcd
        │   ├── kube-apiserver
        │   ├── kube-controller-manager
        │   ├── kube-scheduler
        │   ├── kube-proxy
        │   ├── CoreDNS
        │   └── Flannel CNI
        └── Helm
```

------------------------------------------------------------------------

# 2. Pré-requisitos

Confirme o Ubuntu:

``` bash
cat /etc/os-release
```

Esperado:

``` text
VERSION_ID="20.04"
VERSION_CODENAME=focal
```

No PowerShell, confirme que a distribuição usa WSL2:

``` powershell
wsl -l -v
```

Exemplo:

``` text
NAME             STATE      VERSION
Ubuntu-20.04     Running    2
```

------------------------------------------------------------------------

# 3. Habilitar systemd no WSL2

Dentro do Ubuntu:

``` bash
cat > /etc/wsl.conf <<'EOF'
[boot]
systemd=true
EOF
```

Saia:

``` bash
exit
```

No PowerShell:

``` powershell
wsl --shutdown
wsl -d Ubuntu-20.04
```

Confirme:

``` bash
ps -p 1 -o comm=
```

Esperado:

``` text
systemd
```

Se ainda aparecer `init`, confirme a versão do WSL no PowerShell:

``` powershell
wsl --version
```

------------------------------------------------------------------------

# 4. Instalação do Docker Engine

## 4.1 Dependências

``` bash
apt update
apt install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
```

## 4.2 Chave e repositório Docker

``` bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc

chmod a+r /etc/apt/keyrings/docker.asc
```

``` bash
cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: focal
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
```

## 4.3 Instalar

``` bash
apt update

apt install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

## 4.4 Iniciar serviços

``` bash
systemctl enable --now containerd
systemctl enable --now docker
```

Validação:

``` bash
docker --version
docker compose version
systemctl status docker --no-pager
docker run hello-world
```

------------------------------------------------------------------------

# 5. Erro: Cannot connect to the Docker daemon

Sintoma:

``` text
docker: Cannot connect to the Docker daemon at unix:///var/run/docker.sock.
Is the docker daemon running?
```

Diagnóstico:

``` bash
systemctl status docker
```

Solução:

``` bash
systemctl start docker
systemctl enable docker
```

Teste novamente:

``` bash
docker run hello-world
```

Se `systemctl` não funcionar, verifique se o WSL está realmente usando
systemd:

``` bash
ps -p 1 -o comm=
```

------------------------------------------------------------------------

# 6. Preparar containerd para Kubernetes

Crie configuração:

``` bash
mkdir -p /etc/containerd
containerd config default > /etc/containerd/config.toml
```

Configure cgroup via systemd:

``` bash
sed -i \
  's/SystemdCgroup = false/SystemdCgroup = true/' \
  /etc/containerd/config.toml
```

Reinicie:

``` bash
systemctl restart containerd
```

Valide:

``` bash
grep SystemdCgroup /etc/containerd/config.toml
```

Esperado:

``` text
SystemdCgroup = true
```

------------------------------------------------------------------------

# 7. Configuração de kernel e rede

``` bash
cat > /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF
```

``` bash
modprobe overlay
modprobe br_netfilter
```

Configure sysctl:

``` bash
cat > /etc/sysctl.d/k8s.conf <<EOF
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
```

Aplicar:

``` bash
sysctl --system
```

------------------------------------------------------------------------

# 8. Desabilitar SWAP

O kubelet pode falhar por causa do swap do WSL2.

Temporariamente:

``` bash
swapoff -a
```

Valide:

``` bash
swapon --show
cat /proc/swaps
```

`swapon --show` deve ficar vazio.

## 8.1 Desabilitar swap permanentemente no WSL2

No Windows, crie/edite:

``` text
%UserProfile%\.wslconfig
```

Conteúdo:

``` ini
[wsl2]
swap=0
```

Depois, no PowerShell:

``` powershell
wsl --shutdown
```

Reabra a distribuição e valide:

``` bash
swapon --show
```

------------------------------------------------------------------------

# 9. Instalar Kubernetes

Instale dependências:

``` bash
apt-get update
apt-get install -y apt-transport-https ca-certificates curl gpg
mkdir -p -m 755 /etc/apt/keyrings
```

Adicione a chave do repositório Kubernetes da versão desejada. Exemplo
utilizado no laboratório:

``` bash
curl -fsSL \
  https://pkgs.k8s.io/core:/stable:/v1.36/deb/Release.key \
  | gpg --dearmor \
  -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
```

``` bash
echo \
'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.36/deb/ /' \
> /etc/apt/sources.list.d/kubernetes.list
```

Instale:

``` bash
apt-get update
apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl
```

Valide:

``` bash
kubeadm version
kubectl version --client
kubelet --version
```

------------------------------------------------------------------------

# 10. Inicializar o cluster

Obtenha o IP do WSL:

``` bash
WSL_IP=$(hostname -I | awk '{print $1}')
echo "$WSL_IP"
```

Inicialize:

``` bash
kubeadm init \
  --apiserver-advertise-address="$WSL_IP" \
  --pod-network-cidr=10.244.0.0/16 \
  --cri-socket=unix:///run/containerd/containerd.sock
```

Configure kubectl para root:

``` bash
mkdir -p /root/.kube
cp /etc/kubernetes/admin.conf /root/.kube/config
chmod 600 /root/.kube/config

export KUBECONFIG=/etc/kubernetes/admin.conf
```

------------------------------------------------------------------------

# 11. Erro kubeadm: context deadline / bootstrap admin.conf

Erro observado:

``` text
error execution phase wait-control-plane:
cannot obtain client without bootstrap:
could not bootstrap the admin user in file admin.conf:
unable to create ClusterRoleBinding:
client rate limiter Wait returned an error:
rate: Wait(n=1) would exceed context deadline
```

No caso diagnosticado, o kubelet estava morrendo porque o swap do WSL
permanecia ativo.

Verifique:

``` bash
journalctl -u kubelet -n 100 --no-pager
```

Erro decisivo:

``` text
failed to run Kubelet:
running with swap on is not supported
```

Solução:

``` bash
swapoff -a
systemctl restart containerd
systemctl restart kubelet
```

Valide:

``` bash
systemctl status kubelet --no-pager
```

Se precisar refazer uma inicialização realmente incompleta:

``` bash
kubeadm reset -f

rm -rf /etc/cni/net.d
rm -rf /root/.kube
rm -rf /etc/kubernetes
rm -rf /var/lib/etcd

systemctl restart containerd
systemctl restart kubelet
```

Depois execute novamente o `kubeadm init`.

> Não faça `reset` automaticamente se o API Server, etcd e kubelet já
> estiverem funcionando. Primeiro diagnostique o estado existente.

------------------------------------------------------------------------

# 12. Erro kubelet em auto-restart

Sintoma:

``` text
Active: activating (auto-restart)
Result: exit-code
```

Diagnóstico:

``` bash
journalctl -u kubelet -n 80 --no-pager
```

No laboratório, a causa foi:

``` text
Swap is on
/dev/sdc
failed to run Kubelet:
running with swap on is not supported
```

Solução:

``` bash
swapoff -a
systemctl restart kubelet
```

------------------------------------------------------------------------

# 13. Erro RuntimeConfig / CRI

Mensagem observada:

``` text
RuntimeConfig from runtime service failed
unknown method RuntimeConfig for service runtime.v1.RuntimeService
```

O kubelet informou em seguida que usaria o `cgroupDriver` da própria
configuração.

Verifique prioritariamente:

``` bash
grep SystemdCgroup /etc/containerd/config.toml
grep cgroupDriver /var/lib/kubelet/config.yaml
```

Ideal:

``` text
SystemdCgroup = true
cgroupDriver: systemd
```

Reinicie se necessário:

``` bash
systemctl restart containerd
systemctl restart kubelet
```

------------------------------------------------------------------------

# 14. Erro RBAC: kubernetes-admin não pode listar nodes

Sintoma:

``` text
Error from server (Forbidden):
nodes is forbidden:
User "kubernetes-admin" cannot list resource "nodes"
```

Isso pode ocorrer quando o `kubeadm init` chega ao control-plane, mas
falha antes de concluir a criação dos bindings administrativos.

Use temporariamente:

``` bash
export KUBECONFIG=/etc/kubernetes/super-admin.conf
```

Verifique:

``` bash
kubectl get nodes
kubectl get clusterrolebinding kubeadm-cluster-admins
```

Se o binding não existir:

``` bash
kubectl create clusterrolebinding kubeadm-cluster-admins \
  --clusterrole=cluster-admin \
  --group=kubeadm:cluster-admins
```

Volte:

``` bash
export KUBECONFIG=/etc/kubernetes/admin.conf
```

Valide:

``` bash
kubectl auth can-i '*' '*'
kubectl get nodes
```

Esperado:

``` text
yes
```

------------------------------------------------------------------------

# 15. Instalar Flannel CNI

``` bash
kubectl apply -f \
  https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

Acompanhe:

``` bash
kubectl get pods -n kube-flannel -w
```

Esperado:

``` text
kube-flannel-ds-xxxxx   1/1   Running
```

------------------------------------------------------------------------

# 16. Erro Flannel: 10.96.0.1:443 connection refused

Erro observado:

``` text
Failed to create SubnetManager:
Get "https://10.96.0.1:443/...":
dial tcp 10.96.0.1:443: connect: connection refused
```

Diagnóstico:

``` bash
kubectl get ds -n kube-system
```

No caso encontrado:

``` text
No resources found in kube-system namespace.
```

O `kube-proxy` não havia sido criado porque a execução original do
`kubeadm init` terminou antes da fase de addons.

Instale apenas essa fase:

``` bash
kubeadm init phase addon kube-proxy \
  --kubeconfig=/etc/kubernetes/admin.conf
```

Valide:

``` bash
kubectl get ds -n kube-system
kubectl get pods -n kube-system
```

Teste o Service IP:

``` bash
curl -k https://10.96.0.1:443
```

Uma resposta HTTP 401/403 do API Server é positiva neste teste:
significa que a conexão chegou ao servidor e foi rejeitada apenas por
autenticação/autorização.

Depois reinicie o Flannel:

``` bash
kubectl rollout restart daemonset kube-flannel-ds -n kube-flannel
kubectl get pods -n kube-flannel -w
```

------------------------------------------------------------------------

# 17. Erro kubectl logs: nodes/proxy Forbidden

Sintoma:

``` text
Error from server (Forbidden):
user=kube-apiserver-kubelet-client,
verb=get,
resource=nodes,
subresource(s)=[proxy]
```

Use `super-admin.conf`:

``` bash
export KUBECONFIG=/etc/kubernetes/super-admin.conf
```

Crie o binding:

``` bash
kubectl create clusterrolebinding kube-apiserver-kubelet-api-admin \
  --clusterrole=system:kubelet-api-admin \
  --user=kube-apiserver-kubelet-client
```

Volte:

``` bash
export KUBECONFIG=/etc/kubernetes/admin.conf
```

Valide:

``` bash
kubectl auth can-i get nodes/proxy \
  --as=kube-apiserver-kubelet-client
```

Esperado:

``` text
yes
```

Agora:

``` bash
kubectl logs -n kube-flannel \
  -l app=flannel \
  --all-containers \
  --tail=100
```

------------------------------------------------------------------------

# 18. CoreDNS ausente

Diagnóstico:

``` bash
kubectl get deployment -n kube-system coredns
```

Se retornar:

``` text
NotFound
```

execute:

``` bash
kubeadm init phase addon coredns \
  --kubeconfig=/etc/kubernetes/admin.conf
```

Valide:

``` bash
kubectl get deployment -n kube-system coredns
kubectl get pods -n kube-system -o wide
```

Teste DNS:

``` bash
kubectl run dns-test \
  --image=busybox:1.36 \
  --restart=Never \
  --rm -it \
  -- nslookup kubernetes.default.svc.cluster.local
```

------------------------------------------------------------------------

# 19. Single-node: permitir workloads no control-plane

Para um laboratório com apenas um nó:

``` bash
kubectl taint nodes --all node-role.kubernetes.io/control-plane-
```

Valide:

``` bash
kubectl describe node | grep -i Taints
```

Esperado:

``` text
Taints: <none>
```

------------------------------------------------------------------------

# 20. Instalar Helm

A instalação por `raw.githubusercontent.com` pode falhar em redes que
retornam HTTP 503.

Método APT:

``` bash
apt-get update
apt-get install -y curl gpg apt-transport-https
```

Baixe e valide a chave:

``` bash
HELM_BUILDKITE_APT_KEY_ID="DDF78C3E6EBB2D2CC223C95C62BA89D07698DBC6"

curl -fsSL \
  https://packages.buildkite.com/helm-linux/helm-debian/gpgkey \
  > /tmp/helm.gpg

test "$(gpg --show-keys --with-colons /tmp/helm.gpg \
  | awk -F: '$1 == "fpr" {print $10}' | head -n 1)" \
  = "$HELM_BUILDKITE_APT_KEY_ID" \
  || { echo "ERRO: fingerprint inesperado da chave Helm"; exit 1; }
```

Instale a chave:

``` bash
cat /tmp/helm.gpg \
  | gpg --dearmor \
  | tee /usr/share/keyrings/helm.gpg >/dev/null
```

Adicione o repositório:

``` bash
echo \
"deb [signed-by=/usr/share/keyrings/helm.gpg] https://packages.buildkite.com/helm-linux/helm-debian/any/ any main" \
> /etc/apt/sources.list.d/helm-stable-debian.list
```

Instale:

``` bash
apt-get update
apt-get install -y helm
```

Valide:

``` bash
helm version
helm list -A
```

------------------------------------------------------------------------

# 21. Erro Helm/GitHub HTTP 503

Erro:

``` text
curl: (22) The requested URL returned error: 503
```

Exemplo:

``` bash
curl -fsSL \
  https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 \
  | bash
```

Isso indica indisponibilidade/bloqueio no caminho até
`raw.githubusercontent.com`, não necessariamente falha do Helm.

Solução utilizada: instalar via repositório APT hospedado no Buildkite,
conforme a seção anterior.

O mesmo tipo de 503 também pode afetar:

``` powershell
wsl --list --online
wsl --install -d Ubuntu-20.04
```

quando o catálogo do WSL hospedado no GitHub Raw não está acessível.

------------------------------------------------------------------------

# 22. Erro PowerShell ao usar `<Nome> <Diretorio> <RootFS>`

Comando incorreto:

``` powershell
wsl --import <Nome> <Diretorio> <RootFS> --version 2
```

Erro:

``` text
Operador '<' reservado para uso futuro.
```

Os campos entre `< >` são placeholders, não devem ser digitados
literalmente.

Exemplo correto:

``` powershell
wsl --import Ubuntu-20.04 `
  C:\WSL\Ubuntu-20.04 `
  C:\WSL-Install\ubuntu-focal-rootfs.tar.gz `
  --version 2
```

------------------------------------------------------------------------

# 23. Erro WSL ERROR_FILE_NOT_FOUND no --import

Sintoma:

``` text
Wsl/ERROR_FILE_NOT_FOUND
```

O arquivo RootFS informado não existe.

Verifique:

``` powershell
Get-Item C:\WSL-Install\ubuntu-focal-rootfs.tar.gz
```

Somente execute `wsl --import` quando o arquivo estiver presente.

Um `.tar.gz` não é executável; não tente executá-lo digitando seu
caminho no PowerShell.

------------------------------------------------------------------------

# 24. Comandos WSL executados dentro do Linux

Sintoma:

``` text
Unknown command: --install
WSL
Wsman Shell commandLine
```

Isso ocorre porque `wsl` dentro do Linux pode resolver para outro
programa chamado WSL/Wsman.

Comandos como:

``` powershell
wsl -l -v
wsl --shutdown
wsl --install
```

devem normalmente ser executados no **PowerShell do Windows**.

De dentro do Ubuntu, se necessário:

``` bash
/mnt/c/Windows/System32/wsl.exe -l -v
```

------------------------------------------------------------------------

# 25. Checklist final

Execute:

``` bash
echo "=== SYSTEMD ==="
ps -p 1 -o comm=

echo "=== SWAP ==="
swapon --show

echo "=== DOCKER ==="
docker --version
docker compose version
systemctl is-active docker

echo "=== CONTAINERD ==="
containerd --version
systemctl is-active containerd
grep SystemdCgroup /etc/containerd/config.toml

echo "=== KUBERNETES ==="
kubectl version --client
kubeadm version
kubelet --version

echo "=== NODE ==="
kubectl get nodes -o wide

echo "=== PODS ==="
kubectl get pods -A -o wide

echo "=== SERVICES ==="
kubectl get svc -A

echo "=== HELM ==="
helm version
helm list -A
```

Estado desejado:

``` text
systemd                       OK
swap                          desabilitado
Docker                        running
containerd                    running
SystemdCgroup                 true
Kubernetes node               Ready
kube-apiserver                Running
etcd                          Running
kube-controller-manager       Running
kube-scheduler                Running
kube-proxy                    Running
Flannel                       Running
CoreDNS                       Running
Helm                          operacional
```

------------------------------------------------------------------------

# 26. Teste final de workload

Crie NGINX:

``` bash
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --type=NodePort --port=80
```

Valide:

``` bash
kubectl get deployment
kubectl get pods -o wide
kubectl get svc
```

Teste dentro do cluster:

``` bash
kubectl run curl-test \
  --image=curlimages/curl \
  --restart=Never \
  --rm -it \
  -- curl http://nginx
```

Se retornar a página do NGINX, a cadeia está funcional:

``` text
containerd
   ↓
kubelet
   ↓
Flannel
   ↓
kube-proxy
   ↓
CoreDNS
   ↓
Service
   ↓
Pod NGINX
```

------------------------------------------------------------------------

# 27. Resumo dos erros encontrados

  --------------------------------------------------------------------------------------------------------
  Erro                                    Causa principal          Solução
  --------------------------------------- ------------------------ ---------------------------------------
  `Cannot connect to Docker daemon`       daemon Docker parado     `systemctl enable --now docker`

  `init(Ubuntu...)` no PID 1              systemd desabilitado     `/etc/wsl.conf` + `wsl --shutdown`

  kubelet `auto-restart`                  swap WSL2 ativo          `swapoff -a`; `.wslconfig` com `swap=0`

  `wait-control-plane context deadline`   kubelet não conseguia    corrigir swap/runtime e repetir fase
                                          permanecer ativo         necessária

  `kubernetes-admin ... Forbidden`        RBAC administrativo      `super-admin.conf` + ClusterRoleBinding
                                          incompleto               

  `nodes/proxy Forbidden`                 API server sem binding   `system:kubelet-api-admin`
                                          para kubelet API         

  Flannel `10.96.0.1:443 refused`         kube-proxy ausente       `kubeadm init phase addon kube-proxy`

  CoreDNS `NotFound`                      fase addon não concluída `kubeadm init phase addon coredns`

  Helm/GitHub `503`                       GitHub Raw               instalar Helm via APT/Buildkite
                                          indisponível/bloqueado   

  `wsl <Nome>` ParserError                placeholders digitados   substituir por valores reais
                                          literalmente             

  `WSL_E_DISTRO_NOT_FOUND`                nome incorreto da distro verificar com `wsl -l -v`

  `ERROR_FILE_NOT_FOUND` no import        RootFS inexistente       baixar/verificar arquivo antes do
                                                                   import

  Wsman `Unknown command --install`       comando WSL executado    executar `wsl.exe` no PowerShell
                                          dentro do Linux          
  --------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

# 28. Referências oficiais

-   Docker Engine --- Ubuntu:
    https://docs.docker.com/engine/install/ubuntu/
-   Kubernetes --- kubeadm:
    https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/
-   Kubernetes --- instalação kubeadm:
    https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/
-   Kubernetes --- fases kubeadm:
    https://kubernetes.io/docs/reference/setup-tools/kubeadm/kubeadm-init-phase/
-   Kubernetes --- RBAC:
    https://kubernetes.io/docs/reference/access-authn-authz/rbac/
-   Kubernetes --- kubelet authn/authz:
    https://kubernetes.io/docs/reference/access-authn-authz/kubelet-authn-authz/
-   Helm --- instalação: https://helm.sh/docs/intro/install/
-   Microsoft --- systemd no WSL:
    https://learn.microsoft.com/windows/wsl/systemd
-   Microsoft --- configuração WSL:
    https://learn.microsoft.com/windows/wsl/wsl-config

------------------------------------------------------------------------

## Observações de compatibilidade

Este tutorial reproduz um laboratório em Ubuntu 20.04.6 LTS/WSL2.
Versões de Docker, Kubernetes, Helm e seus repositórios mudam com o
tempo. Em novas instalações, confirme a versão Kubernetes desejada e os
repositórios oficiais antes de executar os comandos.

Para ambientes de produção, WSL2 não substitui uma topologia Linux
dedicada/multi-node. O ambiente descrito aqui é especialmente adequado
para desenvolvimento, experimentação, CI local, Helm, xApps, Open RAN e
laboratórios Kubernetes.
