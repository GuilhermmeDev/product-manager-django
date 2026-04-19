# CRM System

Sistema de gestão de vendas e produtos com suporte a múltiplos roles de usuário. Desenvolvido em Django com interface minimalista e funcionalidades completas de CRUD.

## Requisitos

- Python 3.8+
- Django 3.2+
- SQLite (padrão) ou PostgreSQL

## Instalação

```bash
# Clonar repositório
git clone <repository-url>
cd crm_complete

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Aplicar migrações
python manage.py migrate

# Criar superuser (owner)
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

Acesse em `http://localhost:8000`

## Estrutura do Projeto

```
crm_complete/
├── core/                      # Aplicação principal
│   ├── models.py             # Modelos de dados
│   ├── views.py              # Lógica das views
│   ├── urls.py               # Rotas
│   ├── forms.py              # Formulários
│   └── decorators.py         # Decoradores de permissão
├── templates/                # Templates HTML
│   ├── base.html             # Template base
│   ├── dashboard.html        # Dashboard
│   ├── customer_dashboard.html
│   ├── products/             # Templates de produtos
│   ├── categories/           # Templates de categorias
│   ├── sales/                # Templates de vendas
│   ├── users/                # Templates de usuários
│   └── reports/              # Templates de relatórios
└── crm_complete/             # Configuração Django
```

## Modelos de Dados

### User
- Herda de `AbstractUser` do Django
- Campos: `username`, `email`, `password`, `first_name`, `last_name`, `phone`, `role`
- Roles: `owner` (administrador) ou `customer` (cliente)

### Category
- `name`: Nome da categoria

### Product
- `name`: Nome do produto
- `description`: Descrição
- `price`: Preço em BRL
- `quantity`: Quantidade em estoque
- `category`: Referência para Category
- `created_at`, `updated_at`: Timestamps

### Sale
- `user`: Referência para o cliente que realizou a compra
- `total`: Valor total da venda
- `created_at`: Data da venda

### SaleItem
- `sale`: Referência para Sale
- `product`: Referência para Product
- `quantity`: Quantidade comprada
- `price`: Preço unitário no momento da venda

## Funcionalidades por Role

### Owner (Administrador)

**Dashboard**
- Visualizar total de produtos, usuários e receita
- Acesso a ações rápidas

**Produtos**
- Listar, criar, editar e deletar produtos
- Visualizar por categoria

**Categorias**
- Listar, criar, editar e deletar categorias
- Filtrar produtos por categoria

**Usuários**
- Listar e deletar usuários
- Visualizar role de cada usuário

**Vendas**
- Listar todas as vendas do sistema
- Criar nova venda manual
- Pré-selecionar produto ao clicar em "Comprar"

**Relatórios**
- Receita total e últimas 24 horas
- Top 10 produtos mais vendidos
- Produtos com baixo estoque (< 5 unidades)

### Customer (Cliente)

**Dashboard**
- Visualizar produtos disponíveis
- Total de compras realizadas
- Total gasto
- Histórico de compras recentes

**Produtos**
- Listar todos os produtos
- Botão "Comprar" que leva para criar venda com produto pré-selecionado
- Filtrar por categoria

**Vendas**
- Visualizar histórico de suas compras
- Criar nova compra (com dropdown de produtos)
- Quantidade automática debitada do estoque

## Endpoints Principais

### Autenticação
- `POST /register/` - Registrar novo usuário

### Produtos
- `GET /products/` - Listar produtos
- `GET /products?category=<name>` - Filtrar por categoria
- `POST /products/new/` - Criar produto (owner)
- `GET/POST /products/<id>/edit/` - Editar produto (owner)
- `GET/POST /products/<id>/delete/` - Deletar produto (owner)

### Categorias
- `GET /categories/` - Listar categorias
- `POST /categories/new/` - Criar categoria (owner)
- `GET/POST /categories/<id>/edit/` - Editar categoria (owner)
- `GET/POST /categories/<id>/delete/` - Deletar categoria (owner)

### Vendas
- `GET /sales/` - Listar vendas (own para owner, próprias para customer)
- `POST /sales/new/` - Criar venda
- `GET /sales/new?product_id=<id>` - Criar venda com produto pré-selecionado

### Usuários
- `GET /users/` - Listar usuários (owner)
- `GET/POST /users/<id>/delete/` - Deletar usuário (owner)

### Relatórios (owner)
- `GET /reports/revenue/` - Relatório de receita
- `GET /reports/top-products/` - Produtos mais vendidos
- `GET /reports/low-stock/` - Produtos com baixo estoque

## Fluxos Principais

### Registrar Novo Cliente
1. Acessar `/register/`
2. Preencher formulário com validação por campo
3. Usuário criado com role `customer`

### Comprar Produto (Customer)
1. Listar produtos em `/products/`
2. Clicar em "Comprar" no produto
3. Pré-selecionado em `/sales/new/`
4. Adicionar quantidade e confirmar
5. Estoque atualizado automaticamente
6. Venda registrada com total calculado

### Executar Venda Manual (Owner)
1. Acessar `/sales/new/`
2. Selecionar produtos e quantidades
3. Confirmar venda
4. Estoque debitado, venda registrada

## Segurança e Permissões

- Login obrigatório para acessar dashboard e funcionalidades
- Decorador `@owner_required` restringe ações administrativas
- Customers veem apenas suas próprias vendas
- Validação de formulários por campo com mensagens de erro específicas
- CSRF protection ativado em todos os formulários

## Design da Interface

- Minimalista inspirado em GitHub, Linear e Stripe
- Paleta de cores: branco, tons de cinza e azul
- Tailwind CSS para estilização
- Responsive design mobile-first
- Sem gradientes ou estilos desnecessários
- Bordas sutis e espaçamento generoso

## Tecnologias

- **Backend**: Django 3.2+
- **Frontend**: HTML5, Tailwind CSS
- **Banco de Dados**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Autenticação**: Django Authentication System
