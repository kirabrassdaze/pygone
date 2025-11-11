#!/usr/bin/env python
import sys,time,math,time
class Search:
	v_nodes=0;v_depth=0;end_time=0;critical_time=0;tt_bucket={};eval_exact=1;eval_upper=2;eval_lower=3;eval_mate_upper=32767
	def print_stats(self,v_depth,v_score,v_time,v_nodes,v_nps,v_pv):print(f"info depth {v_depth} score cp {v_score} time {v_time} nodes {v_nodes} nps {v_nps} pv {v_pv}",flush=True)
	def reset(self):self.v_nodes=0;self.v_depth=0;self.end_time=0;self.critical_time=0;self.tt_bucket.clear()
	def iterative_search(self,local_board):
		start_time=time.time();local_score=local_board.rolling_score
		for v_depth in range(1,100):
			local_score=self.search(local_board,v_depth,-self.eval_mate_upper,self.eval_mate_upper)
			if time.time()<self.critical_time:
				best_move=self.tt_bucket.get(local_board.board_string)
				if best_move:best_move=best_move['tt_move']
			else:break
			elapsed_time=time.time()-start_time;v_nps=math.ceil(self.v_nodes/elapsed_time)if elapsed_time>0 else 1;pv='';counter=1;pv_board=local_board.make_move(best_move)
			while counter<min(6,v_depth):
				counter+=1;pv_entry=self.tt_bucket.get(pv_board.board_string)
				if not pv_entry or not pv_entry['tt_move']:break
				pv_board=pv_board.make_move(pv_entry['tt_move']);pv+=' '+pv_entry['tt_move']
			self.print_stats(str(v_depth),str(math.ceil(local_score)),str(math.ceil(elapsed_time*1000)),str(self.v_nodes),str(v_nps),str(best_move+pv));yield(v_depth,best_move,local_score)
	def search(self,local_board,v_depth,alpha,beta):
		if time.time()>self.critical_time:return-self.eval_mate_upper
		is_pv_node=beta>alpha+1;is_in_check=local_board.in_check(local_board.played_move_count%2==0);v_depth+=is_in_check
		if local_board.repetitions.count(local_board.board_string)>2 or local_board.move_counter>=100:return 0
		if v_depth<=0:return self.q_search(local_board,alpha,beta,200)
		tt_entry=self.tt_bucket.get(local_board.board_string,{'tt_value':2*self.eval_mate_upper,'tt_flag':self.eval_upper,'tt_depth':-1,'tt_move':None});self.v_nodes+=1;original_alpha=alpha
		if tt_entry['tt_depth']>=v_depth and tt_entry['tt_move']and not is_pv_node:
			if tt_entry['tt_flag']==self.eval_exact or tt_entry['tt_flag']==self.eval_lower and tt_entry['tt_value']>=beta or tt_entry['tt_flag']==self.eval_upper and tt_entry['tt_value']<=alpha:return tt_entry['tt_value']
		if not is_pv_node and not is_in_check and v_depth<=7 and local_board.rolling_score>=beta+100*v_depth:return local_board.rolling_score
		if not is_pv_node and not is_in_check and v_depth<=5:
			cut_boundary=alpha-385*v_depth
			if local_board.rolling_score<=cut_boundary:
				if v_depth<=2:return self.q_search(local_board,alpha,alpha+1,200)
				local_score=self.q_search(local_board,cut_boundary,cut_boundary+1,200)
				if local_score<=cut_boundary:return local_score
		best_score=-self.eval_mate_upper-1;local_score=-self.eval_mate_upper;is_white=local_board.played_move_count%2==0;pieces='RNBQ'if is_white else'rnbq'
		if not is_pv_node and not is_in_check and pieces in local_board.board_string:
			local_score=-self.search(local_board.nullmove(),v_depth-4,-beta,-beta+1)
			if local_score>=beta:return beta
		if not is_pv_node and not is_in_check and tt_entry['tt_depth']>=v_depth and abs(tt_entry['tt_value'])<self.eval_mate_upper and tt_entry['tt_move']:
			local_score=-self.search(local_board.make_move(tt_entry['tt_move']),v_depth-1,-beta,-alpha)
			if local_score>=beta:return beta
		played_moves=0;best_move=None
		for s_move in sorted(local_board.generate_valid_moves(),key=local_board.move_sort,reverse=True):
			moved_board=local_board.make_move(s_move)
			if moved_board.in_check(is_white):continue
			is_quiet=local_board.piece_count==moved_board.piece_count;played_moves+=1;r_depth=1
			if not is_pv_node and is_quiet and v_depth>2 and played_moves>1:r_depth=max(3,math.ceil(math.sqrt(v_depth-1)+math.sqrt(played_moves-1)))
			if r_depth!=1:local_score=-self.search(moved_board,v_depth-r_depth,-alpha-1,-alpha)
			if r_depth!=1 and local_score>alpha or r_depth==1 and not(is_pv_node and played_moves==1):local_score=-self.search(moved_board,v_depth-1,-alpha-1,-alpha)
			if is_pv_node and(played_moves==1 or local_score>alpha):local_score=-self.search(moved_board,v_depth-1,-beta,-alpha)
			if not best_move:best_move=s_move
			if local_score>best_score:
				best_move=s_move;best_score=local_score
				if local_score>alpha:
					alpha=local_score
					if alpha>=beta:break
		if not played_moves:return-self.eval_mate_upper+local_board.played_move_count if is_in_check else 0
		if time.time()<self.critical_time:
			tt_entry['tt_value']=best_score
			if best_move:tt_entry['tt_move']=best_move
			tt_entry['tt_depth']=v_depth
			if best_score<=original_alpha:tt_entry['tt_flag']=self.eval_upper
			elif best_score>=beta:tt_entry['tt_flag']=self.eval_lower
			else:tt_entry['tt_flag']=self.eval_exact
			self.tt_bucket[local_board.board_string]=tt_entry
		else:self.tt_bucket[local_board.board_string]={'tt_value':2*self.eval_mate_upper,'tt_flag':self.eval_upper,'tt_depth':-1,'tt_move':None}
		return best_score
	def q_search(self,local_board,alpha,beta,v_depth):
		if time.time()>self.critical_time:return-self.eval_mate_upper
		if local_board.repetitions.count(local_board.board_string)>2 or local_board.move_counter>=100:return 0
		tt_entry=self.tt_bucket.get(local_board.board_string)
		if tt_entry:
			if tt_entry['tt_flag']==self.eval_exact or tt_entry['tt_flag']==self.eval_lower and tt_entry['tt_value']>=beta or tt_entry['tt_flag']==self.eval_upper and tt_entry['tt_value']<=alpha:return tt_entry['tt_value']
		local_score=local_board.rolling_score
		if v_depth<=0 or local_score>=beta:return local_score
		alpha=max(alpha,local_score);played_moves=0
		for s_move in sorted(local_board.generate_valid_captures(),key=local_board.move_sort,reverse=True):
			moved_board=local_board.make_move(s_move)
			if moved_board.in_check(local_board.played_move_count%2==0):continue
			if played_moves==0:self.v_nodes+=1
			played_moves+=1;local_score=-self.q_search(moved_board,-beta,-alpha,v_depth-1)
			if local_score>alpha:
				alpha=local_score
				if alpha>=beta:return alpha
		return alpha
PIECEPOINTS={'p':85,'n':295,'b':300,'r':700,'q':1350,'k':32767}
ALLPSQT={'p':(0,0,0,0,0,0,0,0,30,30,30,30,30,30,30,30,8,8,17,26,26,17,8,8,5,5,8,24,24,8,5,5,0,0,0,24,24,0,0,0,5,-5,-8,6,6,-8,-5,5,5,8,8,-22,-22,8,8,5,0,0,0,0,0,0,0,0),'n':(-50,-40,-30,-30,-30,-30,-40,-50,-40,-20,0,0,0,0,-20,-40,-30,0,8,13,13,8,0,-30,-30,5,13,18,18,13,5,-30,-30,0,13,18,18,13,0,-30,-30,5,7,13,13,7,5,-30,-40,-20,0,5,5,0,-20,-40,-50,-40,-20,-30,-30,-20,-40,-50),'b':(-20,-10,-10,-10,-10,-10,-10,-20,-10,0,0,0,0,0,0,-10,-10,0,5,10,10,5,0,-10,-10,5,5,10,10,5,5,-10,-10,0,10,10,10,10,0,-10,-10,10,10,10,10,10,10,-10,-10,5,0,0,0,0,5,-10,-20,-10,-40,-10,-10,-40,-10,-20),'r':(10,20,20,20,20,20,20,10,-10,0,0,0,0,0,0,-10,-10,0,0,0,0,0,0,-10,-10,0,0,0,0,0,0,-10,-10,0,0,0,0,0,0,-10,-10,0,0,0,0,0,0,-10,-10,0,0,0,0,0,0,-10,-10,0,0,10,10,10,0,-10),'q':(-40,-20,-20,-10,-10,-20,-20,-40,-20,0,0,0,0,0,0,-20,-20,0,10,10,10,10,0,-20,-10,0,10,10,10,10,0,-10,0,0,10,10,10,10,0,-10,-20,10,10,10,10,10,0,-20,-20,0,10,0,0,0,0,-20,-40,-20,-20,-10,-10,-20,-20,-40),'k':(-50,-40,-30,-20,-20,-30,-40,-50,-30,-20,-10,0,0,-10,-20,-30,-30,-10,20,30,30,20,-10,-30,-30,-10,30,40,40,30,-10,-30,-30,-10,30,40,40,30,-10,-30,-10,-20,-20,-20,-20,-20,-20,-10,20,20,0,0,0,0,20,20,20,20,35,0,0,10,35,20)}
for(set_piece,set_board)in ALLPSQT.items():prow=lambda row:(0,)+tuple(piece+PIECEPOINTS[set_piece]for piece in row)+(0,);ALLPSQT[set_piece]=sum((prow(set_board[column*8:column*8+8])for column in range(8)),());ALLPSQT[set_piece]=(0,)*20+ALLPSQT[set_piece]+(0,)*20
def get_moves(piece):
	if piece=='k':return[(0,10),(0,-10),(1,0),(-1,0),(1,10),(1,-10),(-1,10),(-1,-10)]
	elif piece=='q':return[(0,10),(0,-10),(1,0),(-1,0),(1,10),(1,-10),(-1,10),(-1,-10)]
	elif piece=='r':return[(0,10),(0,-10),(1,0),(-1,0)]
	elif piece=='b':return[(1,10),(1,-10),(-1,10),(-1,-10)]
	elif piece=='n':return[(1,-20),(-1,-20),(2,-10),(-2,-10),(1,20),(-1,20),(2,10),(-2,10)]
	else:return[(0,-10),(1,-10),(-1,-10)]
def number_to_letter(to_number):return chr(to_number+96)
def print_to_terminal(print_string):print(print_string,flush=True)
def print_stats(v_depth,v_score,v_time,v_nodes,v_nps,v_pv):print_to_terminal(f"info depth {v_depth} score cp {v_score} time {v_time} nodes {v_nodes} nps {v_nps} pv {v_pv}")
def unpack_coordinate(uci_coordinate):return coordinate_to_position(uci_coordinate[0:2]),coordinate_to_position(uci_coordinate[2:4])
def position_to_coordinate(board_position):return number_to_letter(board_position%10)+str(abs(board_position//10-10))
def coordinate_to_position(coordinate):return 10*(abs(int(coordinate[1])-8)+2)+(ord(coordinate[0])-97)+1
class Board:
	board_string='';played_move_count=0;repetitions=[];white_castling=[True,True];black_castling=[True,True];white_king_position='e1';black_king_position='e8';rolling_score=0;piece_count=32;en_passant='';move_counter=0
	def __init__(self):self.board_state='.....................rnbqkbnr..pppppppp..--------..--------..--------..--------..PPPPPPPP..RNBQKBNR.....................'
	def mutate_board(self,board_position,piece):l_board_state=self.board_state;self.board_state=l_board_state[:board_position]+piece+l_board_state[board_position+1:]
	def apply_move(self,uci_coordinate):
		l_board_state=self.board_state;is_white=self.played_move_count%2==0;self.move_counter+=1;from_number,to_number=unpack_coordinate(uci_coordinate);from_piece=l_board_state[from_number].lower()
		if l_board_state[to_number]!='-':self.move_counter=0
		self.mutate_board(to_number,l_board_state[from_number]);self.mutate_board(from_number,'-');set_en_passant=False
		if from_piece=='p':
			self.move_counter=0;set_en_passant=abs(from_number-to_number)==20;en_passant_offset=-1 if is_white else 1
			if set_en_passant:self.en_passant=uci_coordinate[0:1]+str(int(uci_coordinate[3:4])+en_passant_offset)
			elif uci_coordinate[2:4]==self.en_passant:self.mutate_board(to_number-10*en_passant_offset,'-')
			elif len(uci_coordinate)>4:self.mutate_board(to_number,uci_coordinate[4:5].upper()if is_white else uci_coordinate[4:5])
		elif from_piece=='k':
			if is_white:self.white_king_position=uci_coordinate[2:4]
			else:self.black_king_position=uci_coordinate[2:4]
			if abs(to_number-from_number)==2:self.mutate_board(to_number+(1 if to_number>from_number else-2),'-');self.mutate_board(from_number+(to_number-from_number)//2,'R'if is_white else'r')
		if not set_en_passant:self.en_passant=''
		self.board_string=self.str_board();self.piece_count=self.get_piece_count()
	def make_move(self,uci_coordinate):
		board=self.board_copy();board.rolling_score=self.rolling_score+self.calculate_score(uci_coordinate)
		if'e1'in uci_coordinate:board.white_castling=[False,False]
		elif'a1'in uci_coordinate:board.white_castling[0]=False
		elif'h1'in uci_coordinate:board.white_castling[1]=False
		if'e8'in uci_coordinate:board.black_castling=[False,False]
		elif'a8'in uci_coordinate:board.black_castling[0]=False
		elif'h8'in uci_coordinate:board.black_castling[1]=False
		board.apply_move(uci_coordinate);board.played_move_count+=1;board.rolling_score=-board.rolling_score;board.repetitions.append(board.board_string);return board
	def nullmove(self):' allows for a quick way to let other side move ';board=self.board_copy();board.played_move_count+=1;board.rolling_score=-self.rolling_score;return board
	def board_copy(self):' copy the board, does not copy the score ';board=Board();board.played_move_count=self.played_move_count;board.white_king_position=self.white_king_position;board.black_king_position=self.black_king_position;board.board_string=self.board_string;board.piece_count=self.piece_count;board.en_passant=self.en_passant;board.move_counter=self.move_counter;board.board_state=self.board_state;board.repetitions=self.repetitions.copy();board.white_castling=self.white_castling.copy();board.black_castling=self.black_castling.copy();return board
	def get_piece_count(self):return 64-self.board_string.count('-')
	def is_endgame(self):return self.piece_count<14 or self.piece_count<20 and'q'not in self.board_string.lower()
	def move_sort(self,uci_coordinate):return self.calculate_score(uci_coordinate,True)
	def calculate_score(self,uci_coordinate,sorting=False):
		is_white=self.played_move_count%2==0;p_offset=-10 if is_white else 10;p_piece='P'if is_white else'p';is_endgame=self.is_endgame();l_board_state=self.board_state;from_number,to_number=unpack_coordinate(uci_coordinate);offset=0 if is_white else 119;to_offset=abs(to_number-offset);from_offset=abs(from_number-offset);local_score=0;from_piece=l_board_state[from_number].lower();to_piece=l_board_state[to_number].lower();local_score+=ALLPSQT[from_piece][to_offset]-ALLPSQT[from_piece][from_offset]
		if to_piece!='-':local_score+=ALLPSQT[to_piece][to_offset]
		if from_piece=='p':
			if uci_coordinate[2:4]==self.en_passant:local_score+=ALLPSQT[from_piece][to_offset]
			elif len(uci_coordinate)>4:promote=uci_coordinate[4:5];local_score+=ALLPSQT[promote][to_offset]-ALLPSQT['p'][to_offset]
			if self.passer_pawn(from_number):local_score+=10
			if self.stacked_pawn(from_number):local_score-=15
		elif from_piece=='k':
			if abs(to_number-from_number)==2:
				if to_number>from_number:local_score+=ALLPSQT['r'][to_offset-1]-ALLPSQT['r'][to_offset+1]
				else:local_score+=ALLPSQT['r'][to_offset+1]-ALLPSQT['r'][to_offset-2]
				local_score+=10
			else:local_score-=20
		return local_score
	def passer_pawn(self,board_position):
		is_white=self.played_move_count%2==0;p_offset=-10 if is_white else 10;start_position=board_position+p_offset;piece_count=1
		while 20<=start_position<=100:
			if not self.board_state[start_position]in'-.':return False
			start_position+=p_offset
		return True
	def stacked_pawn(self,board_position):
		is_white=self.played_move_count%2==0;p_offset=-10 if is_white else 10;p_piece='P'if is_white else'p';start_position=board_position+p_offset
		while 20<=start_position<=100:
			if self.board_state[start_position]==p_piece:return True
			start_position+=p_offset
		return False
	def str_board(self):return self.board_state+str(self.played_move_count%2)
	def generate_valid_captures(self):return self.generate_valid_moves(True)
	def generate_valid_moves(self,captures_only=False):
		'Return list of valid (maybe illegal) moves';offset=1
		if self.played_move_count%2==0:is_white=True;max_row=81;min_row=31;valid_pieces='prnbqk-'
		else:is_white=False;max_row=31;min_row=81;valid_pieces='PRNBQK-'
		for(board_position,piece)in enumerate(self.board_state):
			if piece in'-.'or is_white==piece.islower():continue
			start_coordinate=position_to_coordinate(board_position);piece_lower=piece.lower()
			if piece=='p':offset=-1
			if not captures_only:
				if piece=='K':
					if self.white_castling[1]and self.board_state[96:99]=='--R'and not any(self.attack_position(is_white,coordinate)for coordinate in['e1','f1','g1']):yield start_coordinate+'g1'
					if self.white_castling[0]and self.board_state[91:95]=='R---'and not any(self.attack_position(is_white,coordinate)for coordinate in['e1','d1','c1']):yield start_coordinate+'c1'
				elif piece=='k':
					if self.black_castling[1]and self.board_state[26:29]=='--r'and not any(self.attack_position(is_white,coordinate)for coordinate in['e8','f8','g8']):yield start_coordinate+'g8'
					if self.black_castling[0]and self.board_state[21:25]=='r---'and not any(self.attack_position(is_white,coordinate)for coordinate in['e8','d8','c8']):yield start_coordinate+'c8'
				elif piece_lower=='p'and max_row<=board_position<max_row+8 and self.board_state[board_position+-10*offset]=='-'and self.board_state[board_position+-20*offset]=='-':yield start_coordinate+position_to_coordinate(board_position+-20*offset)
			for piece_move in get_moves(piece_lower):
				to_position=board_position+piece_move[0]+piece_move[1]*offset
				while 20<to_position<99:
					eval_piece=self.board_state[to_position]
					if not captures_only or captures_only and eval_piece not in'-.':
						dest=position_to_coordinate(to_position)
						if piece_lower=='p':
							if board_position in range(min_row,min_row+8)and piece_move[0]==0 and eval_piece=='-'or board_position in range(min_row,min_row+8)and piece_move[0]!=0 and eval_piece!='-'and eval_piece in valid_pieces:
								for prom in'qrbn':yield start_coordinate+dest+prom
							elif piece_move[0]==0 and eval_piece=='-'or piece_move[0]!=0 and eval_piece!='-'and eval_piece in valid_pieces or dest==self.en_passant:yield start_coordinate+dest
						elif eval_piece in valid_pieces:yield start_coordinate+dest
					if eval_piece!='-'or piece_lower in'knp':break
					to_position=to_position+piece_move[0]+piece_move[1]*offset
	def in_check(self,is_white):king_position=self.white_king_position if is_white else self.black_king_position;return self.attack_position(is_white,king_position)
	def attack_position(self,is_white,coordinate):
		offset=1;valid_pieces='PRNBQK-'if is_white else'prnbqk-';attack_position=coordinate_to_position(coordinate)
		for(board_position,piece)in enumerate(self.board_state):
			if piece in'-.'or is_white==piece.isupper():continue
			if piece=='p':offset=-1
			piece=piece.lower()
			for piece_move in get_moves(piece):
				if piece=='p'and not piece_move[0]:continue
				to_position=board_position+piece_move[0]+offset*piece_move[1]
				while 20<to_position<99:
					eval_piece=self.board_state[to_position]
					if eval_piece in valid_pieces and to_position==attack_position:return True
					if eval_piece!='-'or piece in'knp':break
					to_position=to_position+piece_move[0]+offset*piece_move[1]
		return False
def print_to_terminal(print_string):print(print_string,flush=True)
def fen_to_board_state(fen):
	parts=fen.split();placement,side,castling,ep=parts[0],parts[1],parts[2],parts[3];board=[' ']*120;rows=placement.split('/')
	for(rank_idx,row)in enumerate(rows):
		file_idx=0;rank_start=21+rank_idx*10
		for ch in row:
			if ch.isdigit():file_idx+=int(ch)
			else:board[rank_start+file_idx]=ch;file_idx+=1
	for i in range(120):
		if i<20 or i>=100 or i%10 in(0,9):board[i]='.'
		elif board[i]==' ':board[i]='-'
	board_state=''.join(board);return board_state,side,castling,ep
def main():
	game_board=Board();searcher=Search()
	while 1:
		try:
			line=input()
			if line=='quit':sys.exit()
			elif line=='uci':print_to_terminal('pygone 1.6.5\nuciok')
			elif line=='ucinewgame':game_board=Board();searcher.reset()
			elif line=='isready':print_to_terminal('readyok')
			elif line.startswith('setoption'):0
			elif line.startswith('position fen'):
				parts=line.split()
				if'moves'in parts:moves_index=parts.index('moves');fen=' '.join(parts[2:moves_index]);moves=parts[moves_index+1:]
				else:fen=' '.join(parts[2:]);moves=[]
				game_board.board_state,side,castling,ep=fen_to_board_state(fen);game_board.en_passant=ep if ep!='-'else None;game_board.white_to_move=side=='w';game_board.played_move_count=0 if game_board.white_to_move else 1;game_board.white_castling=['K'in castling,'Q'in castling];game_board.black_castling=['k'in castling,'q'in castling]
				for move in moves:game_board=game_board.make_move(move)
			elif line.startswith('print'):
				for row in range(12):position=row*10;print(game_board.board_state[position:position+10])
				print(game_board.played_move_count,game_board.in_check(game_board.played_move_count%2==0))
			elif line.startswith('position'):
				moves=line.split();game_board=Board()
				for position_move in moves[3:]:game_board=game_board.make_move(position_move)
			elif line.startswith('go'):
				searcher.v_depth=30;move_time=1e8;is_white=game_board.played_move_count%2==0;args=line.split()
				for(key,arg)in enumerate(args):
					if arg=='wtime'and is_white or arg=='btime'and not is_white:move_time=int(args[key+1])/1e3
					elif arg=='depth':searcher.v_depth=int(args[key+1])
				searcher.critical_time=time.time()+max(.75,move_time-1);move_time=max(2.2,move_time/28);searcher.end_time=time.time()+move_time;searcher.critical_time=min(searcher.end_time,searcher.critical_time);searcher.v_nodes=0;s_move=None
				for(v_depth,s_move,best_score)in searcher.iterative_search(game_board):
					if v_depth>=searcher.v_depth or time.time()>=searcher.end_time:break
				print_to_terminal(f"bestmove {str(s_move)}")
		except(KeyboardInterrupt,SystemExit):sys.exit()
		except Exception as exc:print_to_terminal(exc);raise
main()