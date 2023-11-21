from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# Suposições para a otimização de preços
PRECO_BASE = 10  # Preço base para todos os itens
FATOR_DEMANDA = 0.5  # Fator de ajuste baseado na demanda
FATOR_ESTOQUE = 0.3  # Fator de ajuste baseado no estoque

db = SQLAlchemy()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)

class ItemEstoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Item {self.nome}>'

class Vendas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_item = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f'<Item {self.id_item}>'

with app.app_context():
    db.create_all()

@app.route('/item', methods=['POST'])
def adicionar_item():
    dados = request.json
    novo_item = ItemEstoque(nome=dados['nome'], quantidade=dados['quantidade'])
    db.session.add(novo_item)
    db.session.commit()
    return jsonify({'mensagem': 'Item adicionado ao estoque'}), 201

@app.route('/item', methods=['GET'])
def listar_itens():
    itens = ItemEstoque.query.all()
    resultado = [{'id': item.id, 'nome': item.nome, 'quantidade': item.quantidade} for item in itens]
    return jsonify(resultado)

@app.route('/item/<int:id>', methods=['PUT'])
def atualizar_item(id):
    item = ItemEstoque.query.get_or_404(id)
    dados = request.json
    item.nome = dados['nome']
    item.quantidade = dados['quantidade']
    db.session.commit()
    return jsonify({'mensagem': 'Item atualizado'})

@app.route('/item/<int:id>', methods=['DELETE'])
def deletar_item(id):
    item = ItemEstoque.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'mensagem': 'Item removido do estoque'})

@app.route('/item/comprar/<int:id>', methods=['POST'])
def comprar_item(id):
    item = ItemEstoque.query.get_or_404(id)
    
    if item.quantidade > 0:
        item.quantidade -= 1
        nova_venda = Vendas(id_item=id)

        db.session.add(item)
        db.session.commit()
        return jsonify({'mensagem': 'Item comprado com sucesso'})
    else:
        return jsonify({'message': 'Não foi possivel comprar o item'}), 400

def calcular_preco_otimizado(demanda, quantidade_estoque):
    """
    Calcula o preço otimizado com base na demanda e na quantidade em estoque.
    """
    ajuste_demanda = PRECO_BASE * FATOR_DEMANDA * demanda
    ajuste_estoque = PRECO_BASE * FATOR_ESTOQUE * (1 - quantidade_estoque/100)
    preco_otimizado = PRECO_BASE + ajuste_demanda - ajuste_estoque
    return max(preco_otimizado, PRECO_BASE * 0.5)  # Evita preços negativos ou muito baixos

@app.route('/item/preco/<int:id>', methods=['GET'])
def obter_preco_otimizado(id):
    item = ItemEstoque.query.get_or_404(id)
    # Vamos assumir que a demanda é uma função do item (pode ser baseada em dados históricos)
    demanda = len(Vendas.query.filter_by(id_item=id).all()) 
    preco = calcular_preco_otimizado(demanda, item.quantidade)
    return jsonify({'nome': item.nome, 'preco_otimizado': preco})


if __name__ == '__main__':
    db.create_all()  # Cria o banco de dados e tabelas
    app.run(debug=True)

